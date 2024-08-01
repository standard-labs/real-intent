"""Define a Processor that will keep trying to pull leads until filling the request."""
from bigdbm.process.base import BaseProcessor
from bigdbm.client import BigDBMClient
from bigdbm.schemas import IABJob, UniqueMD5, IntentEvent, MD5WithPII
from bigdbm.validate.base import BaseValidator


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

    def _pull_and_validate(
        self,
        intent_events: list[IntentEvent], 
        n_hems: int, 
        validators: list[BaseValidator]
    ) -> list[MD5WithPII]:
        """
        Pulls and validates the leads from the intent events.
        """
        # Setup for iterative data pulling
        md5s_bank: list[UniqueMD5] = self.client.uniquify_md5s(intent_events)
        return_md5s: list[MD5WithPII] = []

        while len(return_md5s) < n_hems:  # Constantly pull PII until the threshold is hit
            if not md5s_bank:
                break

            n_delta: int = n_hems - len(return_md5s)
            md5s_job: list[UniqueMD5] = md5s_bank[:n_delta]
            md5s_with_pii: list[MD5WithPII] = self.client.pii_for_unique_md5s(md5s_job)

            # Utilize parameterized validators to filter leads
            validator: BaseValidator
            for validator in validators:
                md5s_with_pii = validator.validate(md5s_with_pii)

            # Add post-validated (remaining) leads
            return_md5s.extend(md5s_with_pii)

            # Update tracking
            del md5s_bank[:n_delta]

        return return_md5s

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

        # Run with all validators first
        return_md5s: list[MD5WithPII] = self._pull_and_validate(intent_events, n_hems, self.validators)

        # If we have enough leads, return them
        if len(return_md5s) >= n_hems:
            return return_md5s

        # If we don't have enough leads, try again with fallen back validators
        existing_md5s: list[str] = [i.md5 for i in return_md5s]
        return_md5s += self._pull_and_validate(
            [i for i in intent_events if i.md5 not in existing_md5s],  # only run on events not used
            n_hems - len(return_md5s),  # only the remaining leads needed
            self.required_validators  # only required, no fallback validators
        )

        return return_md5s
