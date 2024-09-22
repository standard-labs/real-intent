"""CSV output but with insights."""
from pandas.core.api import DataFrame as DataFrame
from real_intent.deliver.csv import CSVStringFormatter, OUTPUT_COLUMNS
from real_intent.schemas import MD5WithPII


class CSVWithInsightsFormatter(CSVStringFormatter):
    """
    Format into CSV strings with insights.
    """

    def __init__(self, per_lead_insights: dict[str, str], output_columns: list[str] = OUTPUT_COLUMNS):
        super().__init__(output_columns)
        self.per_lead_insights: dict[str, str] = per_lead_insights

    def _as_dataframe(self, pii_md5s: list[MD5WithPII]) -> DataFrame:
        df = super()._as_dataframe(pii_md5s)
        df["insight"] = df["md5"].map(self.per_lead_insights)

        return df
