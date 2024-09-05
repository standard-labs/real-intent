from real_intent.deliver.csv import CSVStringFormatter
from real_intent.schemas import Gender, MD5WithPII, PII


def create_test_md5_with_pii() -> MD5WithPII:
    pii = PII(
                Id="test_id",
                First_Name="John",
                Last_Name="Doe",
                Address="123 Test St",
                City="Test City",
                State="TS",
                Zip="12345",
                Zip4="2224",
                Fips_State_Code="01",
                Fips_County_Code="002",
                County_Name="Columbia",
                Latitude="34.1234",
                Longitude="-87.1234",
                Address_Type="Residential",
                Cbsa="12345",
                Census_Tract="123456",
                Census_Block_Group="1",
                Census_Block="1",
                Gender=Gender.MALE,
                SCF="123",
                DMA="333",
                MSA="222",
                Congressional_District="7",
                HeadOfHousehold="Yes",
                Birth_Month_and_Year="01/1990",
                Age="30",
                Prop_Type="Single Family",
                Email_Array=["john@example.com"],
                mobile_phones=[],
                Children_HH="2",
                Credit_Range="Good",
                Income_HH="100000-150000",
                Net_Worth_HH="500000-1000000",
                Home_Owner="Yes",
                Marital_Status="Married",
                Occupation_Detail="Engineer",
                Median_Home_Value="200000",
                Education="Bachelors",
                Length_of_Residence="5",
                Num_Adults_HH="2",
                Political_Party="Republican",
                Health_Beauty_Products="Yes",
                Cosmetics="Yes",
                Jewelry="Yes",
                Investment_Type="Stocks",
                Investments="Yes",
                Pet_Owner="No",
                Pets_Affinity="Cats",
                Health_Affinity="Fitness",
                Diet_Affinity="Low Carb",
                Fitness_Affinity="Gym",
                Outdoors_Affinity="Hiking",
                Boating_Sailing_Affinity="Yes",
                Camping_Hiking_Climbing_Affinity="Yes",
                Fishing_Affinity="Yes",
                Hunting_Affinity="Yes",
                Aerobics="Yes",
                NASCAR="Yes",
                Scuba="Yes",
                Weight_Lifting="Yes",
                Healthy_Living_Interest="Yes",
                Motor_Racing="Yes",
                Travel_Foreign="Yes",
                Self_Improvement="Yes",
                Walking="Yes",
                Fitness="Yes",
                Ethnicity_Detail="Caucasian",
                Ethnic_Group="Caucasian",
    )

    return MD5WithPII(md5="123abc", sentences=["test sentence"], pii=pii)


def test_csv_string_formatter() -> None:
    formatter = CSVStringFormatter()
    md5s: list[MD5WithPII] = [create_test_md5_with_pii(), create_test_md5_with_pii()]
    
    csv_content = formatter.deliver(md5s)
    print("CSV CONTENT: \n", csv_content)
    
    # Check if the CSV contains the expected headers and data
    expected_header = "test sentence,first_name,last_name,email_1,email_2,email_3,phone_1,phone_1_dnc,phone_2,phone_2_dnc,phone_3,phone_3_dnc,address,city,state,zip_code,gender,age,n_household_children,credit_range,home_owner_status,household_income,marital_status,household_net_worth,occupation,md5"
    assert expected_header in csv_content
    assert "x,John,Doe,john@example.com,,,,,,,,,123 Test St,Test City,TS,12345,Male,30,2,Good,Yes,100000-150000,Married,500000-1000000,Engineer,123abc" in csv_content
    
    # Check if the CSV contains the correct number of rows (header + 2 data rows)
    assert len(csv_content.split('\n')) == 4  # 3 rows + empty line at the end


def test_csv_string_formatter_empty_input() -> None:
    formatter = CSVStringFormatter()
    md5s: list[MD5WithPII] = []
    
    csv_content = formatter.deliver(md5s)
    
    # Check if the CSV is empty for empty input
    assert csv_content == ""

# Add more specific tests for other formatting scenarios as needed