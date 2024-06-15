"""Define a Processor that will keep trying to pull leads until filling the request."""
from bigdbm.process.base import BaseProcessor
from bigdbm.client import BigDBMClient
from bigdbm.schemas import IABJob, UniqueMD5, IntentEvent, MD5WithPII


class FillProcessor(BaseProcessor):
    """
    Processor that pulls 2x as much intent data to start, and then keeps trying more
    to fill the PII.

    1. Pull 2x as much intent data as requested. (adjustable on instantiation)
    2. Request 1x as much PII.
    3. Keep requesting PII on more data until filled.

    Can return less than the requested amount of data if:
    - The PII hit rate is less than 0.5x, as 2x data is not enough.
    - There is not enough intent data returned.
    """

    def __init__(self, bigdbm_client: BigDBMClient, intent_multiplier: float = 2.5) -> None:
        super().__init__(bigdbm_client)
        self.intent_multiplier: float = intent_multiplier

    def process(self, iab_job: IABJob) -> list[MD5WithPII]:
        """
        1. Pull 2x as much intent data as requested. (adjustable on instantiation)
        2. Request 1x as much PII.
        3. Keep requesting PII on more data until filled.

        Can return less than the requested amount of data if:
        - The PII hit rate is less than 0.5x, as 2x data is not enough.
        - There is not enough intent data returned.
        """
        # Extend the number of hems in the initial job
        n_hems: int = iab_job.n_hems  # true amount of PII to return
        iab_job.n_hems = int(iab_job.n_hems * self.intent_multiplier)

        # Run the first job for MD5s
        list_queue_id: int = self.client.create_and_wait(iab_job)
        intent_events: list[IntentEvent] = self.client.retrieve_md5s(list_queue_id)
        md5s_bank: list[UniqueMD5] = self.client.uniquify_md5s(intent_events)

        # Setup for iterative data pulling
        return_md5s: list[MD5WithPII] = []

        # Constantly pull PII until the threshold is hit
        while len(return_md5s) < n_hems:
            if not md5s_bank:
                break

            n_delta: int = n_hems - len(return_md5s)
            md5s_job: list[UniqueMD5] = md5s_bank[:n_delta]
            pii_response: list[MD5WithPII] = self.client.pii_for_unique_md5s(md5s_job)
            return_md5s.extend([md5 for md5 in pii_response if md5.is_valid(iab_job.zips)])

            # Update tracking
            del md5s_bank[:n_delta]

        return return_md5s
    