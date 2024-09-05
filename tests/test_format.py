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
                Health_Beauty_Products="1",
                Cosmetics="1",
                Jewelry="1",
                Investment_Type="1",
                Investments="1",
                Pet_Owner="1",
                Pets_Affinity="1",
                Health_Affinity="1",
                Diet_Affinity="1",
                Fitness_Affinity="1",
                Outdoors_Affinity="1",
                Boating_Sailing_Affinity="1",
                Camping_Hiking_Climbing_Affinity="1",
                Fishing_Affinity="1",
                Hunting_Affinity="1",
                Aerobics="1",
                NASCAR="1",
                Scuba="1",
                Weight_Lifting="1",
                Healthy_Living_Interest="1",
                Motor_Racing="1",
                Travel_Foreign="1",
                Self_Improvement="1",
                Walking="1",
                Fitness="1",
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
    expected_header = "md5,test sentence,first_name,last_name,address,city,state,zip_code,zip4,fips_state_code,fips_county_code,county_name,latitude,longitude,address_type,cbsa,census_tract,census_block_group,census_block,gender,scf,dma,msa,congressional_district,head_of_household,birth_month_and_year,age,prop_type,n_household_children,credit_range,household_income,household_net_worth,home_owner_status,marital_status,occupation,median_home_value,education,length_of_residence,n_household_adults,political_party,health_beauty_products,cosmetics,jewelry,investment_type,investments,pet_owner,pets_affinity,health_affinity,diet_affinity,fitness_affinity,outdoors_affinity,boating_sailing_affinity,camping_hiking_climbing_affinity,fishing_affinity,hunting_affinity,aerobics,nascar,scuba,weight_lifting,healthy_living_interest,motor_racing,foreign_travel,self_improvement,walking,fitness,ethnicity_detail,ethnic_group,email_1,email_2,email_3,phone_1,phone_1_dnc,phone_2,phone_2_dnc,phone_3,phone_3_dnc"
    assert expected_header in csv_content
    assert "123abc,x,John,Doe,123 Test St,Test City,TS,12345,2224,01,002,Columbia,34.1234,-87.1234,Residential,12345,123456,1,1,Male,123,333,222,7,True,01/1990,30,Single Family,2,Good,100000-150000,500000-1000000,Yes,Married,Engineer,200000,Bachelors,5,2,Republican,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,Caucasian,Caucasian,john@example.com,,,,,,,," in csv_content
    
    # Check if the CSV contains the correct number of rows (header + 2 data rows)
    assert len(csv_content.split('\n')) == 4  # 3 rows + empty line at the end


def test_csv_string_formatter_empty_input() -> None:
    formatter = CSVStringFormatter()
    md5s: list[MD5WithPII] = []
    
    csv_content = formatter.deliver(md5s)
    
    # Check if the CSV is empty for empty input
    assert csv_content == ""

# Add more specific tests for other formatting scenarios as needed
