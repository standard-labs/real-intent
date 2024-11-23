from real_intent.deliver.csv import CSVStringFormatter
from real_intent.schemas import MD5WithPII, PII


def test_csv_string_formatter() -> None:
    formatter = CSVStringFormatter()
    # Create two MD5WithPII objects with fake PII data
    md5s: list[MD5WithPII] = [
        MD5WithPII(md5="123abc", sentences=["test sentence"], pii=PII.create_fake(seed=42)),
        MD5WithPII(md5="456def", sentences=["test sentence"], pii=PII.create_fake(seed=43))
    ]
    csv_content = formatter.deliver(md5s)
    print("CSV CONTENT: \n", csv_content)
    
    # Check if the CSV contains the expected headers
    expected_header = "test sentence,md5,first_name,last_name,address,city,state,zip_code,zip4,fips_state_code,fips_county_code,county_name,latitude,longitude,address_type,cbsa,census_tract,census_block_group,census_block,gender,scf,dma,msa,congressional_district,head_of_household,birth_month_and_year,age,prop_type,n_household_children,credit_range,household_income,household_net_worth,home_owner_status,marital_status,occupation,median_home_value,education,length_of_residence,n_household_adults,political_party,health_beauty_products,cosmetics,jewelry,investment_type,investments,pet_owner,pets_affinity,health_affinity,diet_affinity,fitness_affinity,outdoors_affinity,boating_sailing_affinity,camping_hiking_climbing_affinity,fishing_affinity,hunting_affinity,aerobics,nascar,scuba,weight_lifting,healthy_living_interest,motor_racing,foreign_travel,self_improvement,walking,fitness,ethnicity_detail,ethnic_group,email_1,email_2,email_3,phone_1,phone_1_dnc,phone_2,phone_2_dnc,phone_3,phone_3_dnc"
    assert expected_header in csv_content
    
    # Check if the CSV contains the correct number of rows (header + 2 data rows)
    assert len(csv_content.split('\n')) == 4  # 3 rows + empty line at the end


def test_csv_string_formatter_empty_input() -> None:
    formatter = CSVStringFormatter()
    md5s: list[MD5WithPII] = []
    
    csv_content = formatter.deliver(md5s)
    
    # Check if the CSV is empty for empty input
    assert csv_content == ""
