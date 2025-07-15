import os
from dotenv import load_dotenv
from real_intent.deliver.followupboss.ai_fields import AIFollowUpBossDeliverer
from real_intent.schemas import MD5WithPII, PII, Gender, MobilePhone

import logfire
# Only configure logfire if running locally with proper auth
if os.getenv('LOGFIRE_TOKEN'):
    logfire.configure(send_to_logfire=True)
else:
    logfire.configure(send_to_logfire=False)

load_dotenv()

def test_custom_field_matching():

    # Skip test if required environment variables are not available
    required_vars = ['FOLLOWUPBOSS_API_KEY', 'FOLLOWUPBOSS_SYSTEM', 'FOLLOWUPBOSS_SYSTEM_KEY', 'OPENAI_API_KEY']
    for var in required_vars:
        if not os.getenv(var):
            print(f"Skipping test: {var} not set")
            return

    deliverer = AIFollowUpBossDeliverer(
        api_key=os.getenv('FOLLOWUPBOSS_API_KEY'),
        system=os.getenv('FOLLOWUPBOSS_SYSTEM'),
        system_key=os.getenv('FOLLOWUPBOSS_SYSTEM_KEY'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Create sample test data
    sample_pii = PII(
        id='test_id',
        first_name='Test',
        last_name='User',
        address='123 Test St',
        city='Test City',
        state='CA',
        zip_code='12345',
        gender=Gender.MALE,
        age='30',
        emails=['test@example.com'],
        mobile_phones=[],
        occupation='Engineer'
    )

    # Update this to match the MD5 of the customer you want to test
    md5_with_pii = MD5WithPII(
        md5='test_hash',
        sentences=['test_sentence'],
        raw_sentences=['test_sentence'],
        pii=sample_pii
    )
    
    # This will trigger the debug logs
    event_data = deliverer._prepare_event_data(md5_with_pii)

if __name__ == "__main__":
    test_custom_field_matching()
