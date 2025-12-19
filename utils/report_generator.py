import pandas as pd
import numpy as np
import os
import xlsxwriter
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_premium_arrears_report(input_file, output_dir):
    """
    Generates a premium Excel dashboard report for arrears data.
    Adapted from user-provided script for server-side processing.
    
    Args:
        input_file (str): Path to the input CSV/Excel file
        output_dir (str): Directory to save the generated report
        
    Returns:
        tuple: (output_file_path, summary_data_dict)
    """
    if not input_file or not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # --- SETUP PATHS ---
    filename = os.path.basename(input_file)
    name_no_ext = os.path.splitext(filename)[0]
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    output_filename = f"EXECUTIVE_REPORT_{timestamp}.xlsx"
    output_file = os.path.join(output_dir, output_filename)

    logger.info(f"Generating premium report for {filename}...")

    # --- READ DATA ---
    try:
        if input_file.lower().endswith('.csv'):
            df = pd.read_csv(input_file)
        else:
            df = pd.read_excel(input_file)
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise ValueError(f"Could not read file: {e}")

    # --- DATA CLEANING & PREP ---
    required_cols = ['FullNames', 'PhoneNumber', 'Arrears Amount', 'DaysInArrears', 'LoanBalance', 'SalesRep']
    df.columns = [c.strip() for c in df.columns]
    
    for col in required_cols:
        if col not in df.columns:
            # Try fuzzy matching or aliases if strict column names aren't found
            # For now, following exact logic as requested
            df[col] = 0 if 'Amount' in col or 'Days' in col or 'Balance' in col else 'Unknown'

    df_clean = df[required_cols].copy()

    # Numeric conversion
    for col in ['Arrears Amount', 'LoanBalance', 'DaysInArrears']:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)

    # Fill Text
    df_clean['SalesRep'] = df_clean['SalesRep'].fillna('Unassigned').astype(str)
    df_clean['FullNames'] = df_clean['FullNames'].fillna('Unknown Client')

    # Phone Number Formatting
    def clean_phone(x):
        try:
            return str(int(float(x)))
        except:
            return str(x)
    df_clean['PhoneNumber'] = df_clean['PhoneNumber'].apply(clean_phone)

    # BUCKETING LOGIC
    def get_bucket(days):
        if days < 1: return "Current"
        if 1 <= days <= 3: return "1-3 Days"
        if 4 <= days <= 5: return "4-5 Days"
        if 6 <= days <= 9: return "6-9 Days"
        if 10 <= days <= 30: return "10-30 Days"
        return "31+ Days"

    # Numeric ID for Sorting/Grouping
    def get_bucket_id(days):
        if days < 1: return 0
        if 1 <= days <= 3: return 1
        if 4 <= days <= 5: return 2
        if 6 <= days <= 9: return 3
        if 10 <= days <= 30: return 4
        return 5

    df_clean['Bucket'] = df_clean['DaysInArrears'].apply(get_bucket)
    df_clean['BucketID'] = df_clean['DaysInArrears'].apply(get_bucket_id)

    # --- SORTING LOGIC ---
    # 1. SalesRep (A-Z)
    # 2. DaysInArrears (Ascending: 1, 2, 3...)
    df_clean.sort_values(by=['SalesRep', 'DaysInArrears'], ascending=[True, True], inplace=True)

    # --- EXCEL GENERATION ---
    logger.info("Writing Excel report...")
    try:
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        workbook = writer.book
    except Exception as e:
        logger.error(f"Error creating Excel writer: {e}")
        raise

    # --- FORMATTING PALETTE ---
    font_name = 'Segoe UI'
    
    # Formats
    fmt_currency = workbook.add_format({'num_format': '[$KES] #,##0.00', 'border': 1, 'align': 'right', 'font_name': font_name, 'valign': 'vcenter'})
    fmt_number = workbook.add_format({'border': 1, 'align': 'center', 'font_name': font_name, 'valign': 'vcenter'})
    fmt_text = workbook.add_format({'border': 1, 'align': 'left', 'font_name': font_name, 'valign': 'vcenter'})
    fmt_center = workbook.add_format({'border': 1, 'align': 'center', 'font_name': font_name, 'valign': 'vcenter'})
    fmt_percent = workbook.add_format({'num_format': '0.0%', 'border': 1, 'align': 'center', 'font_name': font_name, 'valign': 'vcenter'})
    
    # Headers
    fmt_header_yellow = workbook.add_format({
        'bold': True, 'bg_color': '#FFD966', 'font_color': '#000000', 'border': 1, 
        'align': 'center', 'valign': 'vcenter', 'font_name': font_name, 'font_size': 11
    })
    
    fmt_header_dark = workbook.add_format({
        'bold': True, 'bg_color': '#203764', 'font_color': '#FFFFFF', 'border': 1, 
        'align': 'center', 'valign': 'vcenter', 'font_name': font_name, 'font_size': 12
    })

    # Totals
    fmt_total_row = workbook.add_format({
        'bold': True, 'border': 1, 'bg_color': '#D9D9D9', 'num_format': '[$KES] #,##0.00', 'align': 'right'
    })
    fmt_total_label = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D9D9D9', 'align': 'left'})

    # Merged Bucket Sum Format (Now includes text wrap for Bucket Name + Sum)
    fmt_bucket_sum = workbook.add_format({
        'bold': True, 'border': 1, 'bg_color': '#F2F2F2', 'align': 'center', 'valign': 'vcenter', 
        'font_name': font_name, 'text_wrap': True
    })

    # Bucket Colors (Soft Pastels)
    bucket_colors = {
        0: '#FFFFFF', 1: '#E2EFDA', 2: '#FFF2CC', 
        3: '#FCE4D6', 4: '#F8CBAD', 5: '#FF9999'
    }

    # ==========================================
    # SHEET 1: EXECUTIVE DASHBOARD (Mobile Optimized)
    # ==========================================
    ws_dash = workbook.add_worksheet("Executive Dashboard")
    ws_dash.hide_gridlines(2)
    ws_dash.set_tab_color('#FF0000') 

    # 1. Prepare Summary Data
    pivot_rep = df_clean.groupby('SalesRep').agg(
        Total_Arrears=('Arrears Amount', 'sum'),
        Total_Portfolio=('LoanBalance', 'sum'),
        Client_Count=('FullNames', 'count')
    ).reset_index()
    
    # Calculate Risk %
    pivot_rep['Risk_Pct'] = (pivot_rep['Total_Arrears'] / pivot_rep['Total_Portfolio']).fillna(0)
    pivot_rep = pivot_rep.sort_values('Total_Arrears', ascending=False)

    pivot_bucket = df_clean.groupby('Bucket').agg(
        Total_Arrears=('Arrears Amount', 'sum')
    ).reset_index()

    # 2. Write Summary Data (Hidden)
    ws_dash.write_row('AA1', ['Rep', 'Arrears'], fmt_header_dark)
    ws_dash.write_column('AA2', pivot_rep['SalesRep'], fmt_text)
    ws_dash.write_column('AB2', pivot_rep['Total_Arrears'], fmt_currency)
    
    ws_dash.write_row('AD1', ['Bucket', 'Arrears'], fmt_header_dark)
    ws_dash.write_column('AD2', pivot_bucket['Bucket'], fmt_text)
    ws_dash.write_column('AE2', pivot_bucket['Total_Arrears'], fmt_currency)

    # 3. Create Charts
    chart_rep = workbook.add_chart({'type': 'column'})
    chart_rep.add_series({
        'name': 'Arrears Amount',
        'categories': f"='Executive Dashboard'!$AA$2:$AA${len(pivot_rep)+1}",
        'values':     f"='Executive Dashboard'!$AB$2:$AB${len(pivot_rep)+1}",
        'fill':       {'color': '#4472C4'},
        'data_labels': {'value': False}
    })
    chart_rep.set_title({'name': 'Total Arrears by Sales Rep'})
    
    chart_aging = workbook.add_chart({'type': 'doughnut'})
    chart_aging.add_series({
        'name': 'Aging',
        'categories': f"='Executive Dashboard'!$AD$2:$AD${len(pivot_bucket)+1}",
        'values':     f"='Executive Dashboard'!$AE$2:$AE${len(pivot_bucket)+1}",
        'data_labels': {'percentage': True}
    })
    chart_aging.set_title({'name': 'Portfolio Risk Distribution'})

    # --- MOBILE OPTIMIZATION: VERTICAL STACKING ---
    # Chart 1 at top
    ws_dash.insert_chart('B2', chart_rep, {'x_scale': 1.8, 'y_scale': 1.2})
    
    # Chart 2 below Chart 1
    ws_dash.insert_chart('B18', chart_aging, {'x_scale': 1.8, 'y_scale': 1.2})

    # Table starts further down
    table_start_row = 34

    # 4. Write Scorecard
    dash_headers = ['Rank', 'Sales Rep', 'Client Count', 'Total Arrears', 'Total Portfolio', 'Collection Risk %']
    
    # Write Title
    ws_dash.merge_range(table_start_row-2, 1, table_start_row-2, 6, 'EXECUTIVE ARREARS SCORECARD', 
                       workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'bg_color': '#F2F2F2', 'border': 1}))

    for col, h in enumerate(dash_headers):
        ws_dash.write(table_start_row, col + 1, h, fmt_header_dark)
        
    for i, row in enumerate(pivot_rep.itertuples(), table_start_row+1):
        ws_dash.write(i, 1, i-table_start_row, fmt_number)
        ws_dash.write(i, 2, row.SalesRep, fmt_text)
        ws_dash.write(i, 3, row.Client_Count, fmt_number)
        ws_dash.write(i, 4, row.Total_Arrears, fmt_currency)
        ws_dash.write(i, 5, row.Total_Portfolio, fmt_currency)
        ws_dash.write(i, 6, row.Risk_Pct, fmt_percent)

    ws_dash.conditional_format(table_start_row+1, 6, table_start_row+len(pivot_rep), 6, {
        'type': '3_color_scale',
        'min_color': '#63BE7B', 'mid_color': '#FFEB84', 'max_color': '#F8696B'
    })

    # Smart Auto-Fit Dashboard
    ws_dash.set_column('B:B', 8)  
    ws_dash.set_column('C:C', 25) 
    ws_dash.set_column('D:D', 12) 
    ws_dash.set_column('E:F', 18) 
    ws_dash.set_column('G:G', 15) 

    # ==========================================
    # SHEET 2: DETAILED REPORT
    # ==========================================
    ws = workbook.add_worksheet("Collection Details")
    ws.set_tab_color('#FFC000') 
    ws.freeze_panes(1, 2) 

    # Headers - Removed "Risk Bucket" column, modified order
    headers = ['Sales Rep', 'Client Name', 'Phone', 'Arrears Amount', 'Days Late', 'Risk Category Total', 'Loan Balance']
    for col, h in enumerate(headers):
        ws.write(0, col, h, fmt_header_yellow)
    
    row_num = 1
    col_widths = [len(h) for h in headers] # For auto-fit

    # Iterate by Rep (for Total grouping)
    for rep_name, group in df_clean.groupby('SalesRep', sort=False): 
        
        # Calculate sums per bucket for this rep
        bucket_sums = group.groupby('Bucket')['Arrears Amount'].sum()
        
        # Identify merger ranges
        bucket_ranges = []
        current_b_id = -1
        current_b_name = ""
        start_r = row_num
        count = 0
        
        # Pre-scan group to find merger ranges
        group_rows = list(group.itertuples(index=False))
        for i, row in enumerate(group_rows):
            b_id = row.BucketID 
            b_name = row.Bucket
            
            if b_id != current_b_id and count > 0:
                # Close previous bucket
                b_total = bucket_sums.get(current_b_name, 0)
                bucket_ranges.append((start_r, count, b_total, current_b_name))
                # Reset
                start_r = row_num + i
                count = 1
                current_b_id = b_id
                current_b_name = b_name
            elif count == 0:
                # First item
                current_b_id = b_id
                current_b_name = b_name
                start_r = row_num + i
                count = 1
            else:
                # Continue bucket
                count += 1
                
        # Append last bucket range
        if count > 0:
            b_total = bucket_sums.get(current_b_name, 0)
            bucket_ranges.append((start_r, count, b_total, current_b_name))

        # Write Data Rows
        for i, row in enumerate(group_rows):
            b_id = row.BucketID
            bg_color = bucket_colors.get(b_id, '#FFFFFF')
            
            f_curr = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
            f_text = workbook.add_format({'border': 1})
            f_cent = workbook.add_format({'border': 1, 'align': 'center'})
            
            # --- CONDITIONAL FORMATTING APPLIED TO DAYS LATE ONLY ---
            f_days = workbook.add_format({'border': 1, 'align': 'center', 'bg_color': bg_color, 'bold': True})

            # Data Row (Note: Removed Risk Bucket column from here)
            # Row has: FullNames, PhoneNumber, Arrears Amount, DaysInArrears, LoanBalance, SalesRep, Bucket, BucketID
            # Index depends on dataframe, but we are iterating tuples.
            # Using attribute names from itertuples
            
            ws.write(row_num, 0, row.SalesRep, f_text)
            ws.write(row_num, 1, row.FullNames, f_text)
            ws.write(row_num, 2, row.PhoneNumber, f_cent)
            ws.write(row_num, 3, getattr(row, "_2", 0), f_curr) # Arrears Amount is usually _2 if index=False and 3rd col
            # NOTE: itertuples() naming relies on column names.
            # Columns: FullNames, PhoneNumber, Arrears Amount, DaysInArrears, LoanBalance, SalesRep, Bucket, BucketID
            # _2 is 'Arrears Amount' because of space. 
            
            ws.write(row_num, 4, row.DaysInArrears, f_days) # Color Only Here
            ws.write(row_num, 5, "", f_curr) # Placeholder
            ws.write(row_num, 6, row.LoanBalance, f_curr)

            # Auto-Fit Calculation
            vals_for_width = [row.SalesRep, row.FullNames, row.PhoneNumber, getattr(row, "_2", 0), row.DaysInArrears, 15000, row.LoanBalance]
            for c_idx, val in enumerate(vals_for_width):
                if c_idx < len(col_widths):
                    str_len = len(str(val))
                    if str_len > col_widths[c_idx]:
                        col_widths[c_idx] = str_len
            
            row_num += 1

        # Apply Merges for "Risk Category Total" (Column Index 5)
        for start_r_idx, count_rows, total_val, b_name in bucket_ranges:
            formatted_val = f"{b_name}\nKES {total_val:,.2f}"
            if count_rows > 1:
                ws.merge_range(start_r_idx, 5, start_r_idx + count_rows - 1, 5, formatted_val, fmt_bucket_sum)
            else:
                ws.write(start_r_idx, 5, formatted_val, fmt_bucket_sum)

        # Add Total Row for Rep
        total_arrears = group['Arrears Amount'].sum()
        total_balance = group['LoanBalance'].sum()
        
        ws.write(row_num, 0, f"TOTAL: {rep_name}", fmt_total_label)
        ws.write(row_num, 1, "", fmt_total_row)
        ws.write(row_num, 2, "", fmt_total_row)
        ws.write(row_num, 3, total_arrears, fmt_total_row)
        ws.write(row_num, 4, "", fmt_total_row)
        ws.write(row_num, 5, "", fmt_total_row)
        ws.write(row_num, 6, total_balance, fmt_total_row)

        row_num += 2 

    # --- APPLY INTELLIGENT AUTO-FIT ---
    for i, width in enumerate(col_widths):
        final_width = min(width + 3, 50) 
        ws.set_column(i, i, final_width)
        
    # Manually widen the Category Total column for text wrapping
    ws.set_column(5, 5, 25)

    # --- VISUALS ---
    ws.conditional_format(1, 3, row_num, 3, {'type': 'data_bar', 'bar_color': '#63C384'})
    ws.autofilter(0, 0, row_num, len(headers)-1)

    writer.close()
    
    # Prepare summary for API response
    summary_data = {
        'total_clients': len(df_clean),
        'total_arrears': float(df_clean['Arrears Amount'].sum()),
        'total_portfolio': float(df_clean['LoanBalance'].sum()),
        'sales_reps': df_clean['SalesRep'].nunique(),
        'bucket_distribution': df_clean['Bucket'].value_counts().to_dict(),
        'download_url': output_filename # Simplified, caller will prepend host
    }
    
    return output_filename, summary_data

