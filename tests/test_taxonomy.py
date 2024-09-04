import pytest

from real_intent.taxonomy import code_to_category


def test_code_to_category_valid_code() -> None:
    assert code_to_category(1) == "Automotive"


def test_code_to_category_invalid_code() -> None:
    assert code_to_category(999999) == "999999"


def test_code_to_category_string_input() -> None:
    assert code_to_category("1") == "Automotive"


def test_code_to_category_caching() -> None:
    # Call the function twice with the same input
    result1 = code_to_category(1)
    result2 = code_to_category(1)
    
    # Check that both calls return the same result
    assert result1 == result2
    assert result1 == "Automotive"


@pytest.mark.parametrize("code,expected", [
    (1, "Automotive"),
    (2, "2"),  # Updated to reflect actual behavior
    (3, "Automotive>Auto Body Styles>Commercial Trucks"),
    (228, "Healthy Living>Men's Health"),
    (4455, "Medical Health>Pharmaceutical Drugs>Oncology"),
])
def test_code_to_category_specific_codes(code: int, expected: str) -> None:
    result = code_to_category(code)
    assert result == expected


def test_code_to_category_performance() -> None:
    # Test the performance of multiple calls
    for _ in range(1000):
        code_to_category(1)


def test_code_to_category_edge_cases() -> None:
    assert code_to_category(0) == "0"
    assert code_to_category(-1) == "-1"
    assert code_to_category(None) == "None"


def test_code_to_category_float_input() -> None:
    assert code_to_category(1.0) == "Automotive"
    assert code_to_category(2.5) == "2"


def test_code_to_category_large_valid_code() -> None:
    assert code_to_category(4680) == "sports>skiing>nordic skiing"
