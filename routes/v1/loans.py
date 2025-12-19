"""
Loan processing endpoints with mobile optimizations
Refactored from original app.py with pagination, caching, and field selection
"""
from flask import Blueprint, request, current_app, g
from middleware.auth import require_auth
from middleware.error_handler import ValidationError
from utils.response import mobile_optimized_response, success_response
from utils.pagination import get_pagination_params, create_pagination_response
from utils.validators import validate_file, get_file_extension
import pandas as pd
import os
import tempfile
import logging

# Import original processing modules
from Arreas_collected import ArrearsProcessorAPI as ArrearsProcessor
from arrange_Dues import generate_loan_report as generate_arranged_report
from arrange_arrears import create_enterprise_dashboard
from MTD_unpaid_dues import main as process_unpaid_dues
from MTD_parameters_branch_comparison import BranchPerformanceAnalyzer

logger = logging.getLogger(__name__)

loans_bp = Blueprint('loans', __name__)


def save_uploaded_file(file, filename=None):
    """Save uploaded file to temp directory"""
    if not filename:
        filename = file.filename
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    return filepath


@loans_bp.route('/dormant-arrangement', methods=['POST'])
@require_auth
def process_dormant():
    """
    Process dormant loan arrangements
    
    Form data:
        file: Excel file with branch data
    
    Query params:
        limit: Page size (default: 20)
        after: Pagination cursor
        fields: Comma-separated field names for partial response
    
    Returns:
        Processed dormant arrangement data with pagination
    """
    filepath = None
    try:
        # Validate file upload
        if 'file' not in request.files:
            raise ValidationError('No file provided', field='file')
        
        file = request.files['file']
        validate_file(
            file,
            allowed_extensions=['xlsx', 'xls'],
            max_size=current_app.config['MAX_CONTENT_LENGTH']
        )
        
        # Save file temporarily with unique name to prevent collisions
        import uuid
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}_{file.filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process with existing code
        df = pd.read_excel(filepath)
        
        # Get pagination params
        limit, after_cursor, _ = get_pagination_params()
        
        # Get total count
        total_count = len(df)
        
        # Apply pagination to dataframe BEFORE converting to dict
        start_idx = 0
        if after_cursor:
            from utils.pagination import PaginationCursor
            cursor_data = PaginationCursor.decode_cursor(after_cursor)
            start_idx = cursor_data.get('offset', 0)
        
        end_idx = start_idx + limit + 1  # +1 to check has_more
        paginated_df = df.iloc[start_idx:end_idx]
        
        # Convert paginated data to records
        records = paginated_df.to_dict(orient='records')
        has_more = len(records) > limit
        page_records = records[:limit]
        
        # Generate next cursor
        next_cursor = None
        if has_more:
            from utils.pagination import PaginationCursor
            next_cursor = PaginationCursor.encode_cursor({'offset': end_idx - 1})
        
        result = {
            'data': page_records,
            'pagination': {
                'next_cursor': next_cursor,
                'has_more': has_more,
                'limit': limit,
                'total_count': total_count
            },
            'summary': {
                'total_records': total_count,
                'columns': list(df.columns)
            }
        }
        
        logger.info(f"Processed dormant arrangement: {total_count} records")
        
        return mobile_optimized_response(result, cacheable=False)
    
    except Exception as e:
        logger.error(f"Error processing dormant arrangement: {str(e)}")
        raise
    
    finally:
        # Always clean up temp file
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                logger.warning(f"Failed to cleanup temp file {filepath}: {e}")


@loans_bp.route('/arrears-collected', methods=['POST'])
@require_auth
def process_arrears():
    """
    Process arrears collection data
    
    Form data:
        sod_file: SOD arrears file (CSV)
        current_file: Current arrears file (CSV)
    
    Returns:
        Arrears collection analysis with officer summaries
    """
    sod_path = None
    cur_path = None
    
    try:
        # Validate files
        if 'sod_file' not in request.files or 'current_file' not in request.files:
            raise ValidationError('Both SOD and Current files are required')
        
        sod_file = request.files['sod_file']
        current_file = request.files['current_file']
        
        # Validate file types
        for file in [sod_file, current_file]:
            validate_file(
                file,
                allowed_extensions=['csv'],
                max_size=current_app.config['MAX_CONTENT_LENGTH']
            )
        
        # Save files temporarily with unique names to prevent collisions
        import uuid
        session_id = str(uuid.uuid4())
        sod_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'{session_id}_sod_data.csv')
        cur_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'{session_id}_current_data.csv')
        
        sod_file.save(sod_path)
        current_file.save(cur_path)
        
        # Use ArrearsProcessor
        processor = ArrearsProcessor()
        result = processor.process_data(sod_path, cur_path)
        
        if result is None:
            raise ValidationError('Processing failed - invalid data format')
        
        df_collected, df_merged, officers = result
        
        # Get pagination params
        limit, after_cursor, _ = get_pagination_params()
        
        # Create response with pagination
        collection_records = df_collected.to_dict(orient='records')
        
        paginated_data = create_pagination_response(
            collection_records,
            total_count=len(df_collected),
            limit=limit,
            after_cursor=after_cursor
        )
        
        # Add summary
        paginated_data['summary'] = {
            'total_collected': float(df_collected['Collected'].sum()) if not df_collected.empty else 0,
            'officer_count': len(officers),
            'collection_by_officer': df_collected.groupby('SalesRep')['Collected'].sum().to_dict() if not df_collected.empty else {}
        }
        
        logger.info(f"Processed arrears collection: {len(df_collected)} records")
        
        return mobile_optimized_response(paginated_data, cacheable=False)
    
    except Exception as e:
        logger.error(f"Error processing arrears: {str(e)}")
        raise
    
    finally:
        # Always clean up temp files
        for path in [sod_path, cur_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as e:
                    logger.warning(f"Failed to cleanup temp file {path}: {e}")


@loans_bp.route('/arrange-dues', methods=['POST'])
@require_auth
def arrange_dues():
    """
    Arrange and organize loan dues
    
    Form data:
        file: CSV file with loan data
    
    Returns:
        Organized dues by field officer with pagination
    """
    filepath = None
    
    try:
        if 'file' not in request.files:
            raise ValidationError('No file provided', field='file')
        
        file = request.files['file']
        validate_file(
            file,
            allowed_extensions=['csv'],
            max_size=current_app.config['MAX_CONTENT_LENGTH']
        )
        
        # Save with unique filename to prevent collisions
        import uuid
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}_{file.filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process data
        df = pd.read_csv(filepath)
        
        # Check for required columns
        required_columns = ['FullNames', 'FieldOfficer', 'Amount Due', 'Arrears']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValidationError(f'Missing columns: {", ".join(missing)}')
        
        # Clean numeric columns
        df_processed = df.copy()
        numeric_cols = ['Amount Due', 'Arrears']
        
        for col in numeric_cols:
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(
                    df_processed[col].astype(str).str.replace(r'[^\d\.\-]', '', regex=True),
                    errors='coerce'
                ).fillna(0)
        
        # Group by Field Officer
        grouped = df_processed.groupby('FieldOfficer').agg({
            'FullNames': 'count',
            'Amount Due': 'sum',
            'Arrears': 'sum'
        }).reset_index()
        
        grouped.columns = ['FieldOfficer', 'ClientCount', 'TotalAmountDue', 'TotalArrears']
        
        # Get pagination params
        limit, after_cursor, _ = get_pagination_params()
        
        # Create paginated response
        officer_records = grouped.to_dict(orient='records')
        
        result = create_pagination_response(
            officer_records,
            total_count=len(grouped),
            limit=limit,
            after_cursor=after_cursor
        )
        
        # Add summary
        result['summary'] = {
            'total_clients': len(df_processed),
            'officer_count': len(grouped),
            'total_amount_due': float(df_processed['Amount Due'].sum()),
            'total_arrears': float(df_processed['Arrears'].sum())
        }
        
        logger.info(f"Arranged dues: {len(df_processed)} clients, {len(grouped)} officers")
        
        return mobile_optimized_response(result, cacheable=False)
    
    except Exception as e:
        logger.error(f"Error arranging dues: {str(e)}")
        raise
    
    finally:
        # Always clean up temp file
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                logger.warning(f"Failed to cleanup temp file {filepath}: {e}")


@loans_bp.route('/arrange-arrears', methods=['POST'])
@require_auth
def arrange_arrears():
    """
    Arrange arrears data and generate dashboard metrics
    
    Form data:
        file: CSV/Excel file with arrears data
    
    Returns:
        Arrears arranged by bucket with sales rep summaries
    """
    filepath = None
    
    try:
        if 'file' not in request.files:
            raise ValidationError('No file provided', field='file')
        
        file = request.files['file']
        
        # Save with unique filename to prevent collisions
        import uuid
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}_{file.filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read data
        ext = get_file_extension(file.filename)
        if ext == 'csv':
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        # Clean column names
        df.columns = [c.strip() for c in df.columns]
        
        # Required columns
        required_cols = ['FullNames', 'PhoneNumber', 'Arrears Amount', 'DaysInArrears', 'LoanBalance', 'SalesRep']
        
        # Create missing columns if needed
        for col in required_cols:
            if col not in df.columns:
                if 'Amount' in col or 'Days' in col or 'Balance' in col:
                    df[col] = 0
                else:
                    df[col] = 'Unknown'
        
        df_clean = df[required_cols].copy()
        
        # Ensure numeric columns
        numeric_cols = ['Arrears Amount', 'DaysInArrears', 'LoanBalance']
        for col in numeric_cols:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
        
        # Bucketing logic
        def get_bucket(days):
            if days < 1: return "Current"
            if 1 <= days <= 3: return "1-3 Days"
            if 4 <= days <= 5: return "4-5 Days"
            if 6 <= days <= 9: return "6-9 Days"
            if 10 <= days <= 30: return "10-30 Days"
            return "31+ Days"
        
        df_clean['Bucket'] = df_clean['DaysInArrears'].apply(get_bucket)
        
        # Sort
        df_clean.sort_values(['SalesRep', 'DaysInArrears'], ascending=[True, True], inplace=True)
        
        # Group by SalesRep and Bucket
        summary = df_clean.groupby(['SalesRep', 'Bucket']).agg({
            'FullNames': 'count',
            'Arrears Amount': 'sum',
            'LoanBalance': 'sum'
        }).reset_index()
        
        summary.columns = ['SalesRep', 'Bucket', 'ClientCount', 'TotalArrears', 'TotalPortfolio']
        
        # Get pagination params
        limit, after_cursor, _ = get_pagination_params()
        
        # Paginate summary
        summary_records = summary.to_dict(orient='records')
        
        result = create_pagination_response(
            summary_records,
            total_count=len(summary),
            limit=limit,
            after_cursor=after_cursor
        )
        
        # Overall summary
        result['summary'] = {
            'total_clients': len(df_clean),
            'total_arrears': float(df_clean['Arrears Amount'].sum()),
            'total_portfolio': float(df_clean['LoanBalance'].sum()),
            'sales_reps': df_clean['SalesRep'].nunique(),
            'bucket_distribution': df_clean['Bucket'].value_counts().to_dict()
        }
        
        logger.info(f"Arranged arrears: {len(df_clean)} clients")
        
        return mobile_optimized_response(result, cacheable=False)
    
    except Exception as e:
        logger.error(f"Error arranging arrears: {str(e)}")
        raise
    
    finally:
        # Always clean up temp file
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                logger.warning(f"Failed to cleanup temp file {filepath}: {e}")


@loans_bp.route('/mtd-unpaid-dues', methods=['POST'])
@require_auth
def mtd_unpaid_dues():
    """
    MTD unpaid dues risk analysis
    
    Form data:
        file: CSV/Excel file with loan data
    
    Returns:
        Risk analysis by field officer
    """
    filepath = None
    
    try:
        if 'file' not in request.files:
            raise ValidationError('No file provided', field='file')
        
        file = request.files['file']
        
        # Save with unique filename to prevent collisions
        import uuid
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}_{file.filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Load data
        ext = get_file_extension(file.filename)
        if ext == 'csv':
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        # Standardize columns
        df.columns = [c.strip() for c in df.columns]
        
        # Ensure required columns exist
        required = ["FullNames", "PhoneNumber", "Arrears", "LoanBalance", "FieldOfficer"]
        for col in required:
            if col not in df.columns:
                if col in ["Arrears", "LoanBalance"]:
                    df[col] = 0
                else:
                    df[col] = "Unknown"
        
        df_clean = df[required].copy()
        
        # Convert numeric columns
        numeric_cols = ["Arrears", "LoanBalance"]
        for col in numeric_cols:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
        
        # Risk categorization
        def categorize_risk(row):
            arrears = row['Arrears']
            balance = row['LoanBalance']
            
            if balance == 0:
                return "Unknown"
            
            risk_ratio = arrears / balance if balance > 0 else 0
            
            if risk_ratio > 0.3:
                return "High Risk"
            elif risk_ratio > 0.1:
                return "Medium Risk"
            else:
                return "Low Risk"
        
        df_clean['RiskCategory'] = df_clean.apply(categorize_risk, axis=1)
        
        # Group by officer and risk
        summary = df_clean.groupby(['FieldOfficer', 'RiskCategory']).agg({
            'FullNames': 'count',
            'Arrears': 'sum',
            'LoanBalance': 'sum'
        }).reset_index()
        
        summary.columns = ['FieldOfficer', 'RiskCategory', 'ClientCount', 'TotalArrears', 'TotalPortfolio']
        
        # Get pagination params
        limit, after_cursor, _ = get_pagination_params()
        
        # Paginate
        risk_records = summary.to_dict(orient='records')
        
        result = create_pagination_response(
            risk_records,
            total_count=len(summary),
            limit=limit,
            after_cursor=after_cursor
        )
        
        # Overall statistics
        result['summary'] = {
            'total_clients': len(df_clean),
            'total_arrears': float(df_clean['Arrears'].sum()),
            'total_portfolio': float(df_clean['LoanBalance'].sum()),
            'high_risk_clients': len(df_clean[df_clean['RiskCategory'] == 'High Risk']),
            'medium_risk_clients': len(df_clean[df_clean['RiskCategory'] == 'Medium Risk']),
            'low_risk_clients': len(df_clean[df_clean['RiskCategory'] == 'Low Risk'])
        }
        
        logger.info(f"MTD unpaid dues analysis: {len(df_clean)} clients")
        
        return mobile_optimized_response(result, cacheable=False)
    
    except Exception as e:
        logger.error(f"Error processing MTD unpaid dues: {str(e)}")
        raise
    
    finally:
        # Always clean up temp file
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                logger.warning(f"Failed to cleanup temp file {filepath}: {e}")
