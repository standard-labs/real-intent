"""Follow Up Boss delivery with AI field mapping. Requires OpenAI."""
import openai

from bigdbm.schemas import MD5WithPII
from bigdbm.deliver.followupboss.vanilla import FollowUpBossDeliverer


class AIFollowUpBossDeliverer(FollowUpBossDeliverer):
    """
    Delivers data to FollowUpBoss CRM and uses AI to match fields with the user's
    custom fields. Reads the user's custom fields and matches them with fields in PII data.
    Creates new custom fields for the user's FUB account if they don't exist, and then
    maps the fields in the PII data to the custom fields.
    """

    def _prepare_event_data(self, md5_with_pii: MD5WithPII) -> dict:
        return super()._prepare_event_data(md5_with_pii)
