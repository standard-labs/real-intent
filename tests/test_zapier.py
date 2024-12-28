from real_intent.deliver.zapier import ZapierDeliverer
from real_intent.schemas import PII, MD5WithPII

def test_zapier_deliverer():
    """ This sends it to the Wise Agent Integration Only...

    Couple of things it tests:
    - tests the case where no insights are provided
    - tests the case where no sentences are provided

    Everything else is a required field in the PII schema
    
    """

    pii_1 = PII.create_fake(seed=88)
    test1 = MD5WithPII(
            md5="123",
            sentences=["test sentence for first md5 123", "another test sentence for first md5 123", "third test sentence for first md5 123", "fourth test sentence for first md5 123"],
            pii=pii_1
        )
    
    pii_2 = PII.create_fake(seed=21)
    test2 = MD5WithPII(
            md5="456",
            sentences=["sentence for second md5 456", "sentence for second md5 456", "another sentence for second md5 456"],
            pii=pii_2
        )
    
    pii_3 = PII.create_fake(seed=25)
    test3 = MD5WithPII(
            md5="789",
            sentences=[],
            pii=pii_3
        )
    
    md5_list = [test1, test2, test3]
    
    insights = {
        "123": "Insight for first md5 123",
        "789": "Insight for third md5 789",
    }

    deliverer = ZapierDeliverer(webhook_url="https://hooks.zapier.com/hooks/catch/21128362/28ah4g6/", client_email="test@email.com", per_lead_insights=insights)

    response = deliverer.deliver(md5_list)

    assert response == True
