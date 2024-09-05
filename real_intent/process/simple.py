"""Simple linear pipeline processor. Nothing special, just follow the methods."""
from real_intent.process.base import BaseProcessor
from real_intent.schemas import IABJob, MD5WithPII, IntentEvent, UniqueMD5
from real_intent.validate.base import BaseValidator


class SimpleProcessor(BaseProcessor):
    """Process simply, one method at a time. No quota counting, etc."""

    def _process(self, iab_job: IABJob) -> list[MD5WithPII]:
        """Process the job and return a list of MD5s with PII."""
        list_queue_id: int = self.client.create_and_wait(iab_job)
        intent_events: list[IntentEvent] = self.client.retrieve_md5s(list_queue_id)
        unique_md5s: list[UniqueMD5] = self.client.uniquify_md5s(intent_events)
        md5s_with_pii: list[MD5WithPII] = self.client.pii_for_unique_md5s(unique_md5s)

        validator: BaseValidator
        for validator in self.raw_validators:
            md5s_with_pii = validator.validate(md5s_with_pii)

        return md5s_with_pii
