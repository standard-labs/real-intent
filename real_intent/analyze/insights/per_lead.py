"""Generate insights for each lead."""
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from real_intent.deliver.csv import CSVStringFormatter
from real_intent.schemas import MD5WithPII
from real_intent.analyze.base import BaseAnalyzer
from real_intent.internal_logging import log
from real_intent.analyze.insights.utils import retry_openai_with_backoff


PROMPT = """You are an analyzer of lead data. You're given a list of insights pertaining to an entire set of leads. Your job is to keep the overall insights in mind and generate an insight for an individual lead that came from the full set.
The point of the individual lead insight is to provide a simple, concise, and actionable insight that shows how the individual lead plays into themes or trends that were observed in the full set of insights.
Your individual lead insight should be NO MORE than 2 sentences long.

It's extremely important that you think deeply and critically. Think like a subject-matter expert, thinking through the overall insights and how this individual lead fits into the bigger picture. 
Think about how somebody receiving this lead can make the most of it. Actionable insights are key. 

Your response must be valid JSON with the specified keys. Use the "thinking" key FIRST to think thoroughly and critically through your process, before arriving at your final insight.
"""


class LeadInsight(BaseModel):
    """Insight for a single lead."""
    thinking: str = Field(..., description="Your step by step thought process arriving at the insight")
    md5: str = Field(..., description="MD5 of the lead's PII")
    insight: str = Field(..., description="The insight for the lead")


class PerLeadInsightGenerator(BaseAnalyzer):
    """Generate insights for each lead."""

    def __init__(self, openai_api_key: str, global_insights: str = "") -> None:
        """
        Initialize the PerLeadInsightGenerator.

        Args:
            openai_api_key: The API key for OpenAI.
            global_insights: Global insights to consider for each lead.

        Raises:
            ImportError: If the OpenAI package is not installed.
        """
        self.global_insights = global_insights

        try:
            from openai import OpenAI
        except ImportError:
            log("error", "Failed to import OpenAI. Make sure to install the package with the 'ai' extra.")
            raise ImportError("Please install this package with the 'ai' extra.")
        
        self.openai_client: OpenAI = OpenAI(api_key=openai_api_key)

    def _analyze(self, pii_md5s: list[MD5WithPII]) -> dict[str, str]:
        """
        Generate an insight for each lead. Returns a dictionary of insights.
        Dictionary key is the MD5 of the lead's PII. Value is the string insight.

        Args:
            pii_md5s: List of MD5 hashes with associated PII data.

        Returns:
            A dictionary mapping MD5 hashes to insights.
        """
        with ThreadPoolExecutor(max_workers=5) as executor:
            insights: list[LeadInsight] = list(executor.map(self._analyze_one, pii_md5s))

        return {insight.md5: insight.insight for insight in insights}

    def _analyze_one(self, pii_md5: MD5WithPII) -> LeadInsight:
        """
        Generate an insight for one lead.

        Args:
            pii_md5: MD5 hash with associated PII data for a single lead.

        Returns:
            A LeadInsight object containing the generated insight.
        """
        lead_csv: str = CSVStringFormatter().deliver([pii_md5])

        @retry_openai_with_backoff()
        def generate_insight() -> Any:
            return self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {
                        "role": "system",
                        "content": PROMPT
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Overall Insights:\n\n{self.global_insights}\n\n"
                            f"Lead:\n\n{lead_csv}"
                        )
                    }
                ],
                max_tokens=2000,
                temperature=1,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format=LeadInsight
            )

        try:
            result = generate_insight()
            lead_insight: LeadInsight | None = result.choices[0].message.parsed
            
            if not lead_insight:
                raise ValueError("OpenAI response did not provide a lead insight.")

            # Only one lead is provided, so assume the MD5 can be overriden
            lead_insight.md5 = pii_md5.md5

            return lead_insight

        except Exception as e:
            log("error", f"Failed to generate insight for lead {pii_md5.md5} after retries. Error: {e}")
            return LeadInsight(
                thinking=f"Failed to generate insight for lead {pii_md5.md5} after retries. Error: {e}",
                md5=pii_md5.md5,
                insight="No insight on this lead due to generation failure."
            )
