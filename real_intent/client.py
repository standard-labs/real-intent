"""The Client."""
import requests
from requests import Request, Session
from requests import RequestException

import time
import random
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from threading import Lock

from real_intent.schemas import (
    ConfigDates,
    IABJob,
    IntentEvent,
    UniqueMD5,
    PII,
    MD5WithPII
)
from real_intent.error import BigDBMApiError
from real_intent.internal_logging import log, log_span

class BigDBMClient:
    """
    Client to interface with BigDBM.

    Creating an instance is fairly expensive, as it automatically retrieves
    an access token and configuration dates.

    This class is thread-safe.
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        """Initialize the BigDBM client."""
        self.client_id: str = client_id
        self.client_secret: str = client_secret

        self.timeout_seconds: int = 30

        # Access token declarations (defined by _update_token)
        self._access_token: str = ""
        self._access_token_expiration: int = 0  # unix timestamp
        self._token_lock = Lock()
        self._update_token()

    def _update_token(self) -> None:
        """Update the token inplace."""
        response = requests.post(
            "https://aws-prod-auth-service.bigdbm.com/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        )

        response.raise_for_status()
        response_json = response.json()
        
        with self._token_lock:
            self._access_token = response_json["access_token"]
            self._access_token_expiration = int(time.time() - 10) + response_json["expires_in"]
        
        log("trace", "Updated access token.")

    def _access_token_valid(self) -> bool:
        """
        Returns a boolean of whether the current access token is still active.
        For this to be True, the access token must both exist and be before expiration.
        """
        if not self._access_token:
            return False

        return time.time() < self._access_token_expiration

    def __request(self, request: Request) -> dict:
        """
        Abstracted requesting mechanism handling access token.
        Raises for status automatically. 
        
        Returns a dictionary of the response's JSON.
        """
        if not self._access_token_valid():
            self._update_token()

        # Insert access token into request
        request.headers.update({
            "Authorization": f"Bearer {self._access_token}"
        })

        log(
            "trace", 
            f"Sending request: {
                {
                    'method': request.method,
                    'url': request.url,
                    'headers': request.headers,
                    'data': request.data,
                    'json': request.json
                }
            }"
        )

        try:
            with Session() as session:
                response = session.send(request.prepare(), timeout=self.timeout_seconds)

            response.raise_for_status()
        except RequestException as e:
            # If there's an error, wait and try just once more
            _random_sleep = round(random.uniform(7, 13), 2)
            log("warn", f"Request failed. Waiting {_random_sleep} seconds and trying again. Error: {e}")
            time.sleep(_random_sleep)

            with Session() as session:
                response = session.send(request.prepare(), timeout=self.timeout_seconds)

            if not response.ok:
                log("error", f"Request failed again. Error: {response.text}")

            response.raise_for_status()

        log("trace", f"Received response: {response.text}")
        return response.json()

    def _request(self, request: Request) -> dict:
        """Request abstraction with logging."""
        with log_span(f"Requesting {request.method} {request.url}", _level="trace"):
            return self.__request(request)
    
    def get_config_dates(self) -> ConfigDates:
        """Get the configuration dates from /config."""
        response_json: dict[str, str] = self._request(
            Request(
                method="GET",
                url="https://aws-prod-intent-api.bigdbm.com/intent/configData",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
        )

        config_dates = ConfigDates(
            start_date=response_json["startDate"],
            end_date=response_json["endDate"]
        )
        log("trace", f"Retrieved config dates: {config_dates}")

        return config_dates

    def create_job(self, iab_job: IABJob) -> int:
        """
        Creates IAB job and returns an integer of the job number.
        Does not wait for the job to finish.
        """
        config_dates: ConfigDates = self.get_config_dates()

        log("trace", f"Creating IABJob: {iab_job}")
        request = Request(
            method="POST",
            url="https://aws-prod-intent-api.bigdbm.com/intent/createList",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "StartDate": config_dates.start_date,
                "EndDate": config_dates.end_date,
                **iab_job.as_payload()
            }
        )

        list_queue_id: int = int(self._request(request)["listQueueId"])
        log("trace", f"Created IABJob with listQueueId: {list_queue_id}")

        return list_queue_id

    def get_list_status(self, list_queue_id: int) -> int:
        """Get the processing status of a list."""
        request = Request(
            method="GET",
            url="https://aws-prod-intent-api.bigdbm.com/intent/checkList",
            params={"listQueueId": list_queue_id}
        )

        status_code: int = int(self._request(request)["status"])
        log("trace", f"List ID {list_queue_id} has status code {status_code}")

        return status_code
    
    def wait_until_completion(self, list_queue_id: int) -> None:
        """Wait until a job has finished processing."""
        log("trace", f"Waiting for list ID {list_queue_id} to finish processing.")

        while (status := self.get_list_status(list_queue_id)) != 100:
            if status > 100:
                raise BigDBMApiError(f"List ID {list_queue_id} had an error.")
            
            time.sleep(3)

        return

    def create_and_wait(self, iab_job: IABJob) -> int:
        """
        Create an intent data job and wait until it has processed.
        Returns an (int) of the listQueueId for pulling the results.
        """
        list_queue_id: int = self.create_job(iab_job)

        with log_span(f"Waiting for list {list_queue_id} to finish processing.", _level="trace"):
            self.wait_until_completion(list_queue_id)
        
        return list_queue_id
    
    def _fetch_result_response(self, list_queue_id: int, page_num: int) -> dict:
        """Return the JSON API response when pulling a page's results."""
        request = Request(
            method="POST",
            url="https://aws-prod-intent-api.bigdbm.com/intent/result",
            headers={"Content-Type": "application/json"},
            json={"ListQueueId": list_queue_id, "Page": page_num}
        )

        return self._request(request)

    def _extract_intent_events(self, fetch_result_json: dict) -> list[IntentEvent]:
        """Pull the intent events listed on a job's results page."""
        intent_events = [
            IntentEvent(
                md5=obj["mD5"],
                sentence=obj["sentence"]
            )
            for obj in fetch_result_json["result"]
        ]

        log("trace", f"Extracted intent events: {intent_events}")
        return intent_events

    def _retrieve_md5s(self, list_queue_id: int, n_threads: int = 30) -> list[IntentEvent]:
        """Pull all MD5s from an intent job with multithreads."""
        # First page
        response_json: dict = self._fetch_result_response(list_queue_id, 1)
        page_count: int = response_json["totalCount"]
        intent_events: list[IntentEvent] = self._extract_intent_events(response_json)

        log("trace", f"Retrieved page 1. Pulling {page_count} pages.")

        def pull_page(p: int) -> list[IntentEvent]:
            return self._extract_intent_events(
                self._fetch_result_response(list_queue_id, p)
            )

        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            result = executor.map(
                pull_page,
                range(2, page_count+1)  # ex. [2, 3, 4] for page_count of 4
            )

        page: list[IntentEvent]
        for page in result:
            intent_events.extend(page)

        log("trace", f"Retrieved all {len(intent_events)} intent events.")
        return intent_events

    def retrieve_md5s(self, list_queue_id: int, n_threads: int = 30) -> list[IntentEvent]:
        """Retrieve all MD5s from an intent job. Logged."""
        with log_span(f"Retrieving MD5s from list ID {list_queue_id} with {n_threads} threads", _level="trace"):
            return self._retrieve_md5s(list_queue_id, n_threads=n_threads)

    def uniquify_md5s(self, md5s: list[IntentEvent]) -> list[UniqueMD5]:
        """
        Take a list of raw intent events and create unique MD5s 
        each with all sentences.
        """
        md5s_dict: dict[str, list[str]] = {}

        for md5 in md5s:
            if md5.md5 not in md5s_dict:
                md5s_dict[md5.md5] = []

            md5s_dict[md5.md5].append(md5.sentence)

        # Convert to unique model for auto validation
        key: str
        val: list[str]

        unique_md5s: list[UniqueMD5] = [
            UniqueMD5(md5=key, sentences=val) for key, val in md5s_dict.items()
        ]

        log("trace", f"Uniquified {len(unique_md5s)} MD5s.")
        return unique_md5s

    def check_numbers(self, iab_job: IABJob) -> dict[str, int]:
        """
        Check the availability of data. Specify the max number of hems in the
        IABJob payload. If 1,000 is the n_hems, and there are 10,000 available,
        it'll appear as though only 1,000 are available. But, a 10,000 hem job
        will take far longer. 

        Returns a dictionary with the keys "total" and "unique". All values are
        integers.
        """
        with log_span(f"Checking numbers for job: {iab_job}", _level="info"):
            config_dates: ConfigDates = self.get_config_dates()

            job_payload: dict[str, str] = iab_job.as_payload()
            del job_payload["NumberOfHems"]
            
            request = Request(
                method="POST",
                url="https://aws-prod-intent-api.bigdbm.com/intent/queueCount",                
                headers={"Content-Type": "application/json"},
                json={
                    "StartDate": config_dates.start_date, 
                    "EndDate": config_dates.end_date, 
                    **job_payload
                }
            )
            
            response_json: dict = self._request(request)
            list_queue_id: int = response_json["listQueueId"]

            while (status := self.get_list_status(list_queue_id)) != 100:
                if status > 100:
                    raise BigDBMApiError(f"List ID {list_queue_id} had an error.")

                time.sleep(3)
        
            request_count = Request(
                method="POST",
                url="https://aws-prod-intent-api.bigdbm.com/intent/resultCount",
                headers={"Content-Type": "application/json"},
                json={"ListQueueId": list_queue_id}
            )
            response_count_json: dict = self._request(request_count)

            count_response: dict[str, int] = {
                "total": response_count_json["count"],
                "unique": response_count_json["distinctCount"]
            }

            log(
                "info", 
                f"Checked numbers. Total: {count_response['total']}, Unique: {count_response['unique']}"
            )
            return count_response
        

    def _pull_pii(self, md5s: list[str], output_id: int = 10026) -> dict[str, dict[str, Any]]:
        """Retrieve PII for a list of MD5 objects."""
        log("trace", f"Pulling PII for {len(md5s)} MD5s.")
        request = Request(
            method="POST",
            url="https://aws-prod-dataapi-v09.bigdbm.com/GetDataBy/Md5",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "RequestId": "abcdefg",
                "ObjectList": md5s,
                "OutputId": output_id
            }
        )

        # Each dictionary is a single object in a list
        data: dict[str, list[dict[str, Any]]] = self._request(request)["returnData"]

        # Remove the list and expose only the object
        for key in data:
            data[key] = data[key][0]

        return data

    def pii_for_unique_md5s(self, unique_md5s: list[UniqueMD5]) -> list[MD5WithPII]:
        """
        Pull PII given a list of unique MD5s.

        Note that the resulting list will likely be of shorter len than the input
        given the PII hit rate is often less than 1.00. 
        """
        md5s_list: list[str] = [md5.md5 for md5 in unique_md5s]
        pii_data: dict[str, dict[str, Any]] = self._pull_pii(md5s_list)

        return_md5s: list[MD5WithPII] = []
        md5: UniqueMD5

        for md5 in unique_md5s:
            if not md5.md5 in pii_data:
                continue

            return_md5s.append(
                MD5WithPII(
                    md5=md5.md5,
                    sentences=md5.sentences,
                    pii=PII.from_api_dict(pii_data[md5.md5])
                )
            )

        log(
            "trace", 
            (
                f"Retrieved {len(return_md5s)} PII for {len(unique_md5s)} initial MD5s, "
                f"hit rate: {len(return_md5s) / len(unique_md5s):.2f}"
            )
        )

        return return_md5s


    ''' Can refactor to avoid redudancy in the following functions by using a private function that deals with request and initial processing'''

    def phones_to_pii(self, phones: list[str]) -> list[PII]:
        """Pull PII for a list of phone numbers."""

        log("trace", f"Requesting PII for {len(phones)} phone numbers.")

        request = Request(
                method="POST",
                url="https://aws-prod-dataapi-v09.bigdbm.com/GetDataBy/Phone",
                headers={
                    "Content-Type": "application/json"
                },
                json={
                    "RequestId": "gfedcba",
                    "ObjectList": phones,
                    "OutputId": 10026
                }
            )
        
        data: dict[str, list[dict[str, Any]]] = self._request(request)["returnData"]
    
        for key in data:
            data[key] = data[key][0]

        return_piis: list[PII] = []
        pii: PII
        
        for phone in phones:
            if phone in data:
                pii = PII.from_api_dict(data[phone])
                return_piis.append(pii)

        log("trace", f"Retrieved PII for {len(return_piis)} of {len(phones)} phone numbers.")

        return return_piis


    def ips_to_pii(self, ips: list[str]) -> list[PII]:
        """Pull PII for a list of IP addresses."""

        log("trace", f"Requesting PII for {len(ips)} IP addresses.")

        request = Request(
                method="POST",
                url="https://aws-prod-dataapi-v09.bigdbm.com/GetDataBy/IP",
                headers={
                    "Content-Type": "application/json"
                },
                json={
                    "RequestId": "nmlkjih",
                    "ObjectList": ips,
                    "OutputId": 10026
                }
            )
        
        data: dict[str, list[dict[str, Any]]] = self._request(request)["returnData"]
    
        for key in data:
            data[key] = data[key][0]

        return_piis: list[PII] = []
        pii: PII
        
        for ip in ips:
            if ip in data:
                pii = PII.from_api_dict(data[ip])
                return_piis.append(pii)

        log("trace", f"Retrieved PII for {len(return_piis)} of {len(ips)} phone numbers.")
        

        return return_piis
    

    def pii_to_pii(self, first_name: str, last_name: str, address: str, zip_code: str, sequence: str) -> list[PII]:
        '''
        Pull PII given ONE object containing first name, last name, address, zip code, and sequence
        
        can be refactored to take in a dictionary of the object instead of individual parameters if wanted

        '''

        log("trace", f"Requesting PII for {first_name}, {last_name}, {address}, {zip_code}, {sequence}.")
        

        info_given = {
            "FirstName": first_name,
            "LastName": last_name,
            "Address": address,
            "Zip": zip_code,
            "Sequence": sequence
        }

        request = Request(
            method="POST",
            url="https://aws-prod-dataapi-v09.bigdbm.com/GetDataBy/Pii",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "requestId": "zyxwvu",
                "ObjectList": [info_given],
                "OutputId": 10026
            }
        )

        data: dict[str, list[dict[str, Any]]] = self._request(request)["returnData"]
    
        for key in data:
            data[key] = data[key][0]

        return_piis: list[PII] = []
        pii: PII
        
        if info_given in data:
            pii = PII.from_api_dict(data[info_given])
            return_piis.append(pii)
        
        log("trace", f"Retrieved PII for {first_name}, {last_name}, {address}, {zip_code}, {sequence}.")

        return return_piis
    

        

    

    