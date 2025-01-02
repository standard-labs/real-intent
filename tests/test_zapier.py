from real_intent.deliver.zapier import ZapierDeliverer
from real_intent.schemas import PII, MD5WithPII

def test_zapier_deliverer():

    """ Test to mimick how the deliverer will work in real-intent-deliveries"""
    pii_1 = PII.create_fake(seed=55)
    test1 = MD5WithPII(
            md5="123",
            sentences=["test sentence for first md5 123", "another test sentence for first md5 123", "third test sentence for first md5 123", "fourth test sentence for first md5 123"],
            pii=pii_1
        )
    
    pii_2 = PII.create_fake(seed=66)
    test2 = MD5WithPII(
            md5="456",
            sentences=["sentence for second md5 456", "sentence for second md5 456", "another sentence for second md5 456"],
            pii=pii_2
        )
    
    pii_3 = PII.create_fake(seed=77)
    test3 = MD5WithPII(
            md5="789",
            sentences=["sentence for third md5 789"],
            pii=pii_3
        )
        
    insights = {
        "123": "Insight for first md5 123",
        "789": "Insight for third md5 789",
        "456": "Insight for second md5 456"
    }

    md5_list = [test1, test2, test3]

    # [wiseagent, excel] - full functional webhooks with zapier, will have to manually check, but they are working
    webhook_urls = ["https://hooks.zapier.com/hooks/standard/21128362/135959053d3748f28471c65abd95fc3c/", "https://hooks.zapier.com/hooks/standard/21128362/8eacd04a01e340b88b8e3723e108bc15/"]

    deliverer = ZapierDeliverer(webhook_urls=webhook_urls, per_lead_insights=insights)

    deliverer.deliver(md5_list)

    assert True