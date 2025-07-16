import os
import pytest
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

@pytest.mark.skipif(
    not all([
        os.getenv('FOLLOWUPBOSS_API_KEY'),
        os.getenv('FOLLOWUPBOSS_SYSTEM'), 
        os.getenv('FOLLOWUPBOSS_SYSTEM_KEY'),
        os.getenv('OPENAI_API_KEY')
    ]),
    reason="Required environment variables not set: FOLLOWUPBOSS_API_KEY, FOLLOWUPBOSS_SYSTEM, FOLLOWUPBOSS_SYSTEM_KEY, OPENAI_API_KEY"
)
def test_custom_field_matching():
    deliverer = AIFollowUpBossDeliverer(
        api_key=os.getenv('FOLLOWUPBOSS_API_KEY', 'dummy_api_key'),
        system=os.getenv('FOLLOWUPBOSS_SYSTEM', 'dummy_system'),
        system_key=os.getenv('FOLLOWUPBOSS_SYSTEM_KEY', 'dummy_system_key'),
        openai_api_key=os.getenv('OPENAI_API_KEY', 'dummy_openai_key')
    )
    
    # Create sample test data
    sample_pii = PII.create_fake(seed=42)

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
