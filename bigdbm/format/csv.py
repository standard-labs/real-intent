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
    'intents'
]


class CSVStringFormatter(BaseOutputFormatter):
    """Format into CSV strings."""

    def __init__(self, output_columns: list[str] = OUTPUT_COLUMNS):
        self.output_columns = output_columns

    def format_md5s(self, pii_md5s: list[MD5WithPII]) -> str:
        """
        Convert the unique MD5s into a CSV string.
        Returns empty string if no result.
        """
        if not pii_md5s:
            return ""

        lead_dicts: list[dict[str, Any]] = [
            {
                "md5": md5.md5,
                "intents": ", ".join(md5.sentences),
                **md5.pii.as_lead_export()
            }
            for md5 in pii_md5s
        ]

        # Convert to DataFrame for exporting
        pii_df: pd.DataFrame = pd.DataFrame(lead_dicts)[self.output_columns]

        # Convert to CSV string
        string_io = StringIO()
        pii_df.to_csv(string_io, index=False)
        return string_io.getvalue()
