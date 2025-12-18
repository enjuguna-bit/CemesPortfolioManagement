"""
Shared phone number formatting utilities for Kenyan phone numbers
Provides vectorized operations for efficient processing
"""
import pandas as pd
import re
from typing import List


class PhoneNumberFormatter:
    """Utility class for formatting Kenyan phone numbers"""
    
    # Kenyan phone number pattern: 254XXXXXXXXX
    PHONE_PATTERN = re.compile(r'^254\d{9}$')
    
    @staticmethod
    def normalize_kenyan_phone_vectorized(df: pd.DataFrame, phone_col: str) -> pd.DataFrame:
        """
        Normalize Kenyan phone numbers using vectorized operations
        
        Args:
            df: DataFrame containing phone numbers
            phone_col: Name of the column containing phone numbers
            
        Returns:
            DataFrame with normalized phone numbers
        """
        if phone_col not in df.columns:
            return df
        
        df_copy = df.copy()
        
        # Convert to string and fill NaN
        df_copy[phone_col] = df_copy[phone_col].fillna('').astype(str)
        
        # Remove non-digit characters
        df_copy[phone_col] = df_copy[phone_col].str.replace(r'\D', '', regex=True)
        
        # Apply normalization rules using vectorized operations
        # Rule 1: 07XXXXXXXX (10 digits starting with 07) -> 254XXXXXXXXX
        mask_07 = df_copy[phone_col].str.startswith('07') & (df_copy[phone_col].str.len() == 10)
        df_copy.loc[mask_07, phone_col] = '254' + df_copy.loc[mask_07, phone_col].str[1:]
        
        # Rule 2: 7XXXXXXXX (9 digits starting with 7) -> 254XXXXXXXXX
        mask_7 = df_copy[phone_col].str.startswith('7') & (df_copy[phone_col].str.len() == 9)
        df_copy.loc[mask_7, phone_col] = '254' + df_copy.loc[mask_7, phone_col]
        
        # Rule 3: XXXXXXXXX (9 digits not starting with 0) -> 254XXXXXXXXX
        mask_9digit = (df_copy[phone_col].str.len() == 9) & (~df_copy[phone_col].str.startswith('0'))
        df_copy.loc[mask_9digit, phone_col] = '254' + df_copy.loc[mask_9digit, phone_col]
        
        # Rule 4: 254XXXXXXXXX (12 digits starting with 254) -> keep as is
        mask_254 = df_copy[phone_col].str.startswith('254') & (df_copy[phone_col].str.len() == 12)
        
        # Mark invalid numbers as empty
        valid_mask = mask_07 | mask_7 | mask_9digit | mask_254
        df_copy.loc[~valid_mask & (df_copy[phone_col].str.len() > 0), phone_col] = ''
        
        return df_copy
    
    @staticmethod
    def format_for_display(phone: str) -> str:
        """
        Format phone number for display: 254XXXXXXXXX -> +254 XXX XXX XXX
        
        Args:
            phone: Phone number string
            
        Returns:
            Formatted phone number
        """
        if not phone or not isinstance(phone, str):
            return ""
        
        # Remove non-digits
        phone_digits = re.sub(r'\D', '', phone)
        
        # Check if valid Kenyan number
        if len(phone_digits) == 12 and phone_digits.startswith('254'):
            return f"+254 {phone_digits[3:6]} {phone_digits[6:9]} {phone_digits[9:]}"
        elif len(phone_digits) == 9:
            return f"+254 {phone_digits[0:3]} {phone_digits[3:6]} {phone_digits[6:]}"
        elif len(phone_digits) == 10 and phone_digits.startswith('0'):
            return f"+254 {phone_digits[1:4]} {phone_digits[4:7]} {phone_digits[7:]}"
        else:
            return phone  # Return original if can't format
    
    @staticmethod
    def validate_kenyan_phone(phone: str) -> bool:
        """
        Validate if phone number is a valid Kenyan format
        
        Args:
            phone: Phone number string
            
        Returns:
            True if valid, False otherwise
        """
        if not phone or not isinstance(phone, str):
            return False
        
        # Remove non-digits
        phone_digits = re.sub(r'\D', '', phone)
        
        # Valid if 254XXXXXXXXX format
        return bool(PhoneNumberFormatter.PHONE_PATTERN.match(phone_digits))
    
    @staticmethod
    def count_valid_phones(df: pd.DataFrame, phone_col: str) -> int:
        """
        Count valid phone numbers in a DataFrame column
        
        Args:
            df: DataFrame containing phone numbers
            phone_col: Name of the column containing phone numbers
            
        Returns:
            Count of valid phone numbers
        """
        if phone_col not in df.columns:
            return 0
        
        return df[phone_col].apply(PhoneNumberFormatter.validate_kenyan_phone).sum()
