import os
from dotenv import load_dotenv
from real_intent.deliver.followupboss.ai_fields import AIFollowUpBossDeliverer
from real_intent.schemas import MD5WithPII, PII, Gender, MobilePhone

import logfire
logfire.configure(send_to_logfire=True)

load_dotenv()

def test_custom_field_matching():
    deliverer = AIFollowUpBossDeliverer(
        api_key=os.getenv('FOLLOWUPBOSS_API_KEY'),
        system=os.getenv('FOLLOWUPBOSS_SYSTEM'),
        system_key=os.getenv('FOLLOWUPBOSS_SYSTEM_KEY'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Update this to match the MD5 of the customer you want to test
    md5_with_pii = MD5WithPII(md5='09d64c8963f40ea0b28259ca436131b1', sentences=['In-Market>Real Estate>Property Type>Residential', 'In-Market>Real Estate>Property Type>Residential'], raw_sentences=['In-Market>Real Estate>Property Type>Residential', 'In-Market>Real Estate>Property Type>Residential'], pii=PII(id='1315016397', first_name='Edward', last_name='Bertuccelli', address='13344 Lakeside Ter', city='Cooper City', state='FL', zip_code='33330', zip4='2662', fips_state_code='12', fips_county_code='011', county_name='Broward', latitude=26.0532, longitude=-80.3262, address_type='S', cbsa='33100', census_tract='070316', census_block_group='1', census_block='1012', gender=Gender('Male'), scf='333', dma='528', msa='4992', congressional_district='25', head_of_household='1', birth_month_and_year='08/19/1960', age='64', prop_type='', emails=['ebert33330@yahoo.com', 'golf4funfl@yahoo.com'], mobile_phones=[], n_household_children='1', credit_range='B. 750-799', household_income='R. $400-$499K', household_net_worth='J. Greater than $499,999', home_owner_status='Home Owner', marital_status='Married', occupation='Finance', median_home_value='744800', education='Completed College', length_of_residence='15', n_household_adults='3', political_party='Republican', health_beauty_products='', cosmetics='', jewelry='', investment_type=True, investments='1', pet_owner='', pets_affinity='', health_affinity='1', diet_affinity='', fitness_affinity='1', outdoors_affinity='1', boating_sailing_affinity='', camping_hiking_climbing_affinity='', fishing_affinity='', hunting_affinity='', aerobics='', nascar='', scuba='', weight_lifting='', healthy_living_interest='1', motor_racing='', foreign_travel='', self_improvement='1', walking='', fitness='1', ethnicity_detail='', ethnic_group=''))
    
    # This will trigger the debug logs
    event_data = deliverer._prepare_event_data(md5_with_pii)

if __name__ == "__main__":
    test_custom_field_matching()
