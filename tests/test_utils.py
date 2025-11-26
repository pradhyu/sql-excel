"""Tests for utils.py - sanitize_identifier function."""

import pytest
from utils import sanitize_identifier


class TestSanitizeIdentifier:
    """Test suite for the sanitize_identifier function."""
    
    def test_basic_sanitization(self):
        """Test basic sanitization of spaces and special characters."""
        assert sanitize_identifier("User Name") == "User_Name"
        assert sanitize_identifier("Order ID") == "Order_ID"
        assert sanitize_identifier("Total Amount") == "Total_Amount"
    
    def test_special_characters(self):
        """Test sanitization of various special characters."""
        assert sanitize_identifier("Salary ($)") == "Salary____"
        assert sanitize_identifier("Rate (%)") == "Rate____"
        assert sanitize_identifier("Name (Last, First)") == "Name__Last__First_"
        assert sanitize_identifier("Employee #") == "Employee__"
    
    def test_multiple_spaces(self):
        """Test handling of multiple consecutive spaces."""
        assert sanitize_identifier("First  Name") == "First__Name"
        assert sanitize_identifier("A   B   C") == "A___B___C"
    
    def test_leading_trailing_spaces(self):
        """Test removal of leading and trailing spaces."""
        assert sanitize_identifier("  Name  ") == "Name"
        assert sanitize_identifier(" ID ") == "ID"
    
    def test_numbers(self):
        """Test that numbers are preserved."""
        assert sanitize_identifier("Column123") == "Column123"
        assert sanitize_identifier("Year 2024") == "Year_2024"
    
    def test_underscores_preserved(self):
        """Test that existing underscores are preserved."""
        assert sanitize_identifier("user_id") == "user_id"
        assert sanitize_identifier("first_name") == "first_name"
    
    def test_empty_string(self):
        """Test handling of empty string."""
        result = sanitize_identifier("")
        assert isinstance(result, str)
    
    def test_only_special_characters(self):
        """Test string with only special characters."""
        result = sanitize_identifier("@#$%")
        assert result == "____"
    
    def test_mixed_case_preserved(self):
        """Test that case is preserved."""
        assert sanitize_identifier("FirstName") == "FirstName"
        assert sanitize_identifier("LAST_NAME") == "LAST_NAME"
    
    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        # Unicode characters should be replaced with underscores
        result = sanitize_identifier("Café")
        assert "_" in result or result == "Caf_"
    
    def test_sheet_name_examples(self):
        """Test real-world sheet name examples."""
        assert sanitize_identifier("Sales Data (2024)") == "Sales_Data__2024_"
        assert sanitize_identifier("Employee Records") == "Employee_Records"
        assert sanitize_identifier("Q1 Results") == "Q1_Results"
    
    def test_column_name_examples(self):
        """Test real-world column name examples."""
        assert sanitize_identifier("Full Name") == "Full_Name"
        assert sanitize_identifier("Date of Birth") == "Date_of_Birth"
        assert sanitize_identifier("Is Active?") == "Is_Active_"
