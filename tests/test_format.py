from bigdbm.deliver.csv import CSVStringFormatter
from bigdbm.schemas import MD5WithPII, PII


def create_test_md5_with_pii() -> MD5WithPII:
    pii_dict = {
        "Id": "test_id",
        "First_Name": "John",
        "Last_Name": "Doe",
        "Address": "123 Test St",
        "City": "Test City",
        "State": "TS",
        "Zip": "12345",
        "Email_Array": ["john@example.com"],
        "Gender": "Male",
        "Age": "30",
        "Children_HH": "2",
        "Credit_Range": "Good",
        "Home_Owner": "Yes",
        "Income_HH": "100000-150000",
        "Net_Worth_HH": "500000-1000000",
        "Marital_Status": "Married",
        "Occupation_Detail": "Engineer",
        "Veteran_HH": "0"
    }
    
    pii = PII.from_api_dict(pii_dict)
    return MD5WithPII(md5="123abc", sentences=["test sentence"], pii=pii)


def test_csv_string_formatter() -> None:
    formatter = CSVStringFormatter()
    md5s: list[MD5WithPII] = [create_test_md5_with_pii(), create_test_md5_with_pii()]
    
    csv_content = formatter.deliver(md5s)
    
    # Check if the CSV contains the expected headers and data
    expected_header = "test sentence,first_name,last_name,email_1,email_2,email_3,phone_1,phone_1_dnc,phone_2,phone_2_dnc,phone_3,phone_3_dnc,address,city,state,zip_code,gender,age,n_household_children,credit_range,home_owner_status,household_income,marital_status,household_net_worth,occupation,n_household_veterans,md5"
    assert expected_header in csv_content
    assert "x,John,Doe,john@example.com,,,,,,,,,123 Test St,Test City,TS,12345,Male,30,2,Good,Yes,100000-150000,Married,500000-1000000,Engineer,0,123abc" in csv_content
    
    # Check if the CSV contains the correct number of rows (header + 2 data rows)
    assert len(csv_content.split('\n')) == 4  # 3 rows + empty line at the end


def test_csv_string_formatter_empty_input() -> None:
    formatter = CSVStringFormatter()
    md5s: list[MD5WithPII] = []
    
    csv_content = formatter.deliver(md5s)
    
    # Check if the CSV is empty for empty input
    assert csv_content == ""

# Add more specific tests for other formatting scenarios as needed