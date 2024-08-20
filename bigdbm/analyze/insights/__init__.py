"""Use an LLM to generate insights from PII data."""
from pydantic import BaseModel, Field

from bigdbm.analyze.base import BaseAnalyzer
from bigdbm.schemas import MD5WithPII

from bigdbm.analyze.insights.prompt import SYSTEM_PROMPT
from bigdbm.format.csv import CSVStringFormatter
from bigdbm.validate.base import BaseValidator


class LeadInsights(BaseModel):
    """Insights generated from lead data."""
    thoughts: str = Field(
        ...,
        description=(
            "String of any thinking that'll help you work through the leads, any "
            "patterns, and arrive at your insights. Think of this as a scratchpad you "
            "can use to note down things you notice to be thorough and refined in your "
            "final insights, and to calculate real numbers (percentages etc.)."
        )
    )
    insights: list[str] = Field(
        ...,
        description=(
            "List of strings where each string is a detailed insight derived from "
            "the lead data. These insights focus on IAB intent categories and personal "
            "information of each lead. They provide actionable information to help "
            "understand how to sell to these leads effectively. Insights combine "
            "multiple attributes (e.g., marital status, net worth, and intent "
            "categories) to make informed assumptions about what the leads would want. "
            "The language used is tailored for the person who will be using these "
            "leads, providing critical and analytical observations that can guide "
            "marketing strategies and personalized outreach efforts."
        )
    )


class OpenAIInsightsGenerator(BaseAnalyzer):
    """Generates insights from PII data using OpenAI."""

    def __init__(self, openai_api_key: str):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install this package with the 'openai' extra.")
        
        self.openai_client: OpenAI = OpenAI(api_key=openai_api_key)

    def analyze(self, pii_md5s: list[MD5WithPII]) -> str:
        """
        Analyze the list of MD5s with PII and generate insights using an LLM.

        Args:
            pii_md5s (list[MD5WithPII]): List of MD5 hashes with associated PII data.

        Returns:
            str: Generated insights as a string.
        """
        result = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": CSVStringFormatter().format_md5s(pii_md5s)
                }
            ],
            max_tokens=4095,
            temperature=1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format=LeadInsights
        )

        lead_insights: LeadInsights | None = result.choices[0].message.parsed

        if not lead_insights:
            return "No insights on these leads at the moment."

        # Process insights to create an ordered list
        processed_insights: list[str] = []
        for i, insight in enumerate(lead_insights.insights, start=1):
            # Remove "- " if present at the beginning of the insight
            if insight.startswith("- "):
                insight = insight[2:]

            # Add the ordered list number
            processed_insights.append(f"{i}. {insight}")

        return "\n".join(processed_insights)


class ValidationInclusiveInsightsGenerator(BaseAnalyzer):
    """Generates insights from PII data using OpenAI. Incorporates knowledge of validators."""

    def __init__(
            self, 
            openai_api_key: str, 
            required_validators: list[BaseValidator] = [], 
            fallback_validators: list[BaseValidator] = []
        ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install this package with the 'openai' extra.")
        
        self.openai_client: OpenAI = OpenAI(api_key=openai_api_key)
        self.required_validators: list[BaseValidator] = required_validators
        self.fallback_validators: list[BaseValidator] = fallback_validators

    def extract_validation_info(self) -> str:
        """Pull validation information from the validators."""
        def _remove_keys(vd: dict) -> dict:
            """Remove instance variables from the dictionary that are API creds."""
            return {k: v for k, v in vd.items() if not k.endswith("_key")}

        def _format_validator_info(validator: BaseValidator) -> str:
            """Format the information for a single validator."""
            return (
                f"- {validator.__class__.__name__}: {validator.__class__.__doc__}\n"
                f"Args: {_remove_keys(validator.__dict__)}\n"
            )

        def _get_validators_info(validators: list[BaseValidator], header: str) -> str:
            """Get formatted information for a list of validators."""
            info = f"{header}\n\n"
            info += "".join(_format_validator_info(v) for v in validators)
            return info

        validation_info = _get_validators_info(
            self.required_validators,
            "Required Validators (must be used on leads):"
        )

        validation_info += "\n\n" + _get_validators_info(
            self.fallback_validators,
            "Fallback Validators (attempted at first, removed only if not "
            "enough volume. i.e. not enough volume, try again with only required "
            "validators):"
        )

        return validation_info

    def analyze(self, pii_md5s: list[MD5WithPII]) -> str:
        """
        Analyze the list of MD5s with PII and generate insights using an LLM.

        Args:
            pii_md5s (list[MD5WithPII]): List of MD5 hashes with associated PII data.

        Returns:
            str: Generated insights as a string.
        """
        result = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": CSVStringFormatter().format_md5s(pii_md5s)
                }
            ],
            max_tokens=4095,
            temperature=1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format=LeadInsights
        )

        lead_insights: LeadInsights | None = result.choices[0].message.parsed

        if not lead_insights:
            return "No insights on these leads at the moment."

        # Process insights to create an ordered list
        processed_insights: list[str] = []
        for i, insight in enumerate(lead_insights.insights, start=1):
            # Remove "- " if present at the beginning of the insight
            if insight.startswith("- "):
                insight = insight[2:]

            # Add the ordered list number
            processed_insights.append(f"{i}. {insight}")

        return "\n".join(processed_insights)
