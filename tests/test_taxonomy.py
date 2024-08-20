import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from bigdbm.taxonomy import code_to_category


@pytest.fixture
def mock_taxonomy_df():
    df = pd.DataFrame({
        'IAB_Category_ID': [1, 2, 3],
        'IAB_Category_Name': ['Automotive', 'Auto Body Styles', 'Automotive>Auto Body Styles>Commercial Trucks']
    })
    return MagicMock(spec=pd.DataFrame, __getitem__=lambda self, key: df)


@patch('bigdbm.taxonomy.taxonomy_df')
def test_code_to_category_valid_code(mock_df):
    mock_df.__getitem__.return_value = pd.DataFrame({
        'IAB_Category_ID': [1],
        'IAB_Category_Name': ['Automotive']
    })
    result = code_to_category(1)
    assert isinstance(result, str)
    assert result == "Automotive"


@patch('bigdbm.taxonomy.taxonomy_df')
def test_code_to_category_invalid_code(mock_df):
    mock_df.__getitem__.return_value = pd.DataFrame(columns=['IAB_Category_ID', 'IAB_Category_Name'])
    result = code_to_category(999999)  # Assuming this is an invalid code
    assert result == "999999"  # For invalid codes, it should return the code as a string


def test_code_to_category_string_input():
    # Test with a string input that's not a valid code
    result = code_to_category("Not a code")
    assert result == "Not a code"


@patch('bigdbm.taxonomy.taxonomy_df')
def test_code_to_category_caching(mock_df):
    mock_df.__getitem__.return_value = pd.DataFrame({
        'IAB_Category_ID': [1],
        'IAB_Category_Name': ['Automotive']
    })
    # Test that the function uses caching
    code_to_category.cache_clear()  # Clear the cache before testing
    result1 = code_to_category(1)
    result2 = code_to_category(1)
    assert result1 == result2
    assert code_to_category.cache_info().hits == 1  # Second call should be a cache hit


@pytest.mark.parametrize("code,expected", [
    (1, "Automotive"),
    (2, "Auto Body Styles"),
    (3, "Automotive>Auto Body Styles>Commercial Trucks"),
])
@patch('bigdbm.taxonomy.taxonomy_df')
def test_code_to_category_specific_codes(mock_df, code, expected):
    mock_df.__getitem__.return_value = pd.DataFrame({
        'IAB_Category_ID': [code],
        'IAB_Category_Name': [expected]
    })
    result = code_to_category(code)
    assert result == expected
