"""Simple linear pipeline processor. Nothing special, just follow the methods."""
from bigdbm.process.base import BaseProcessor
from bigdbm.schemas import IABJob, MD5WithPII, IntentEvent, UniqueMD5


class SimpleProcessor(BaseProcessor):
    """Process simply, one method at a time. No quota counting, etc."""

    def process(self, iab_job: IABJob) -> list[MD5WithPII]:
        """Process the job and return a list of MD5s with PII."""
        list_queue_id: int = self.client.create_and_wait(iab_job)
        intent_events: list[IntentEvent] = self.client.retrieve_md5s(list_queue_id)
        unique_md5s: list[UniqueMD5] = self.client.uniquify_md5s(intent_events)
        return [
            md5 for md5 in self.client.pii_for_unique_md5s(unique_md5s)
            if md5.is_valid(iab_job.zips)
        ]
