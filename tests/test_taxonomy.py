import pytest
from bigdbm.taxonomy import code_to_category

def test_code_to_category_valid_code():
    # Test with a valid IAB category code
    result = code_to_category(1)
    assert isinstance(result, str)
    assert result == "Automotive"

def test_code_to_category_invalid_code():
    # Test with an invalid IAB category code
    result = code_to_category(999999)  # Assuming this is an invalid code
    assert result == "999999"  # For invalid codes, it should return the code as a string

def test_code_to_category_string_input():
    # Test with a string input that's not a valid code
    result = code_to_category("Not a code")
    assert result == "Not a code"

def test_code_to_category_caching():
    # Test that the function uses caching
    code_to_category.cache_clear()  # Clear the cache before testing
    result1 = code_to_category(1)
    result2 = code_to_category(1)
    assert result1 == result2
    assert code_to_category.cache_info().hits == 1  # Second call should be a cache hit

@pytest.mark.parametrize("code,expected", [
    (1, "Automotive"),
    (2, "2"),  # Assuming this code doesn't have a mapping
    (3, "Automotive>Auto Body Styles>Commercial Trucks"),
    # Add more test cases here based on your actual IAB categories
])
def test_code_to_category_specific_codes(code, expected):
    result = code_to_category(code)
    assert result == expected

# Note: You might need to mock the pandas read_csv function if you want to avoid
# reading the actual CSV file during testing. This would involve using the
# unittest.mock.patch decorator to replace pd.read_csv with a mock that returns
# a predefined DataFrame.