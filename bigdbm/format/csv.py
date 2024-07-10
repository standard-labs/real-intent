"""Format into CSV strings."""
import pandas as pd

from io import StringIO
from typing import Any

from bigdbm.format.base import BaseOutputFormatter
from bigdbm.schemas import MD5WithPII


OUTPUT_COLUMNS: list[str] = [
    'first_name',
    'last_name',
    'email_1',
    'email_2',
    'email_3',
    'phone_1',
    'phone_1_dnc',
    'phone_2',
    'phone_2_dnc',
    'phone_3',
    'phone_3_dnc',
    'address',
    'city',
    'state',
    'zip_code',
    'gender',
    'age',
    'n_household_children',
    'credit_range',
    'home_owner_status',
    'household_income',
    'marital_status',
    'household_net_worth',
    'occupation',
    'n_household_veterans',
    'md5',
]


class CSVStringFormatter(BaseOutputFormatter):
    """Format into CSV strings."""

    def __init__(self, output_columns: list[str] = OUTPUT_COLUMNS):
        self.output_columns = [] + output_columns

    @staticmethod
    def _unique_sentences(all_md5s: list[MD5WithPII]) -> set[str]:
        """Return unique sentences from all MD5s."""
        unique_sentences: set[str] = set()

        for md5 in all_md5s:
            unique_sentences.update(md5.sentences)

        return unique_sentences

    @staticmethod
    def _intent_columns(current_md5: MD5WithPII, unique_sentences: set[str]) -> dict[str, str]:
        """Keys: 1 column per intent category. Values: x if applies to the person."""
        intent_columns: dict[str, str] = {}

        for sentence in unique_sentences:
            intent_columns[sentence] = "x" if sentence in current_md5.sentences else ""

        return intent_columns

    def format_md5s(self, pii_md5s: list[MD5WithPII]) -> str:
        """
        Convert the unique MD5s into a CSV string.
        Returns empty string if no result.
        """
        if not pii_md5s:
            return ""
            
        # Calculate the unique sentences
        unique_sentences: set[str] = self._unique_sentences(pii_md5s)

        lead_dicts: list[dict[str, Any]] = [
            {
                "md5": md5.md5,
                **self._intent_columns(md5, unique_sentences),
                **md5.pii.as_lead_export()
            }
            for md5 in pii_md5s
        ]

        # Convert to DataFrame for exporting
        self.output_columns[1:1] = (list_sentences := list(unique_sentences))
        pii_df: pd.DataFrame = pd.DataFrame(lead_dicts)[self.output_columns]

        # Rename intent columns for readability
        pii_df.rename(
            columns={sentence: sentence.split(">")[-1] for sentence in list_sentences}, 
            inplace=True
        )

        # Convert to CSV string
        string_io = StringIO()
        pii_df.to_csv(string_io, index=False)
        return string_io.getvalue()
