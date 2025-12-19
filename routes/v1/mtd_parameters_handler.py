"""
MTD Parameters Branch Comparison Endpoint
Handles processing of MTD income, CR, and disbursement files
"""

import os
import io
from flask import request, jsonify
from werkzeug.utils import secure_filename
import logging
import tempfile
from datetime import datetime

# Import the existing MTD analysis logic
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from MTD_parameters_branch_comparison import MTDParametersAPI

logger = logging.getLogger(__name__)


def process_mtd_parameters_endpoint():
    """
    Process MTD parameters (Income, CR, Disbursement) and generate branch comparison
    
    Expected files:
    - income_file: MTD income data (CSV/Excel)
    - cr_file: MTD collection rate data (CSV/Excel)
    - disb_file: MTD disbursement data (CSV/Excel)
    
    Returns:
    - Branch performance rankings with scores
    - Summary statistics
    - Download URL for formatted Excel report
    """
    
    try:
        # Validate file uploads
        if 'income_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Income file is required',
                'details': {'field': 'income_file'}
            }), 400
        
        if 'cr_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'CR file is required',
                'details': {'field': 'cr_file'}
            }), 400
        
        if 'disb_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Disbursement file is required',
                'details': {'field': 'disb_file'}
            }), 400
        
        income_file = request.files['income_file']
        cr_file = request.files['cr_file']
        disb_file = request.files['disb_file']
        
        # Validate filenames
        if income_file.filename == '' or cr_file.filename == '' or disb_file.filename == '':
            return jsonify({
                'success': False,
                'message': 'All files must have valid filenames'
            }), 400
        
        logger.info(f"Processing MTD parameters: income={income_file.filename}, cr={cr_file.filename}, disb={disb_file.filename}")
        
        # Read files into BytesIO objects
        income_stream = io.BytesIO(income_file.read())
        cr_stream = io.BytesIO(cr_file.read())
        disb_stream = io.BytesIO(disb_file.read())
        
        # Initialize analyzer
        analyzer = MTDParametersAPI()
        
        # Load data
        load_result = analyzer.load_data(income_stream, cr_stream, disb_stream)
        if load_result['status'] == 'error':
            return jsonify({
                'success': False,
                'message': load_result['message'],
                'error': load_result.get('error', '')
            }), 400
        
        # Analyze data (sort by performance score descending)
        sort_option = request.args.get('sort', 'score_desc')
        analysis_result = analyzer.analyze_data(sort_option)
        
        if analysis_result['status'] == 'error':
            return jsonify({
                'success': False,
                'message': analysis_result['message'],
                'error': analysis_result.get('error', '')
            }), 500
        
        # Generate Excel report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'reports')
        os.makedirs(static_dir, exist_ok=True)
        
        excel_filename = f"branch_performance_{timestamp}.xlsx"
        excel_path = os.path.join(static_dir, excel_filename)
        
        excel_result = analyzer.export_to_excel(excel_path)
        
        if excel_result['status'] == 'error':
            logger.error(f"Failed to generate Excel: {excel_result.get('error', '')}")
            download_url = None
        else:
            download_url = f"/static/reports/{excel_filename}"
            logger.info(f"Excel report generated: {download_url}")
        
        # Prepare response data matching the Android API model
        # Transform data to match BranchPerformance structure
        branch_data = []
        for item in analysis_result['data']:
            branch_data.append({
                'rank': item['Rank'],
                'branch_name': item['Branch Name'],
                'income': float(item['Income (KES)']),
                'cr_percentage': float(item['CR %']),
                'disbursement': float(item['Disbursement']),
                'performance_score': float(item['Performance Score'])
            })
        
        # Prepare summary matching MTDSummary structure
        summary = {
            'total_branches': analysis_result['summary']['total_branches'],
            'total_income': float(analysis_result['summary']['total_income']),
            'average_cr': float(analysis_result['summary']['avg_cr']),
            'total_disbursement': float(analysis_result['summary']['total_disbursement'])
        }
        
        return jsonify({
            'success': True,
            'message': f"Analysis complete! Processed {len(branch_data)} branches",
            'data': {
                'summary': summary,
                'data': branch_data,
                'download_url': download_url,
                'metadata': analysis_result.get('metadata', {})
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in MTD parameters processing: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Internal server error during MTD processing',
            'error': str(e)
        }), 500
