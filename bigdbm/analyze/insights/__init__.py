"""Use an LLM to generate insights from PII data."""
from pydantic import BaseModel, Field

from bigdbm.analyze.base import BaseAnalyzer
from bigdbm.schemas import MD5WithPII

from bigdbm.analyze.insights.prompt import SYSTEM_PROMPT
from bigdbm.analyze.insights.validator_prompt import SYSTEM_PROMPT as VALIDATOR_PROMPT

from bigdbm.deliver.csv import CSVStringFormatter
from bigdbm.validate.base import BaseValidator
from bigdbm.process.base import BaseProcessor, ProcessValidator


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
            "marketing strategies and personalized outreach efforts. Each insight "
            "should be a complete, self-contained statement without any leading "
            "numbers or bullet points."
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
                    "content": CSVStringFormatter().deliver(pii_md5s)
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
            processed_insights.append(f"{i}. {insight}")

        return "\n".join(processed_insights)


class ValidatedLeadInsights(BaseModel):
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
    validation_insight: str = Field(
        ...,
        description=(
            "Intuitive, in-context insight on the validation process "
            "and its results. Avoid using the validator names themselves, instead "
            "use a high-level approach to describe what validations happened and why. "
            "That said, do be specific about the criteria and the results."
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
            "marketing strategies and personalized outreach efforts. Each insight "
            "should be a complete, self-contained statement without any leading "
            "numbers or bullet points."
        )
    )


class ValidatedInsightsGenerator(BaseAnalyzer):
    """Generates insights from PII data using OpenAI. Incorporates knowledge of validators."""

    def __init__(
            self, 
            openai_api_key: str, 
            processor: BaseProcessor,
        ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install this package with the 'openai' extra.")
        
        self.openai_client: OpenAI = OpenAI(api_key=openai_api_key)
        self.processor: BaseProcessor = processor

    def extract_validation_info(self) -> str:
        """Pull validation information from the validators."""
        def _remove_keys(vd: dict) -> dict:
            """Remove instance variables from the dictionary that are API creds."""
            return {k: v for k, v in vd.items() if not k.endswith("_key")}

        def _format_validator_info(validator: BaseValidator) -> str:
            """Format the information for a single validator."""
            return (
                f"- {validator.__class__.__name__}: {validator.__class__.__doc__.strip()}\n"
                f"\tArgs: {_remove_keys(validator.__dict__)}"
            )

        def _get_validators_info(validators: list[BaseValidator]) -> str:
            """Get formatted information for a list of validators."""
            return "\n".join(_format_validator_info(v) for v in validators)

        all_priorities: list[int] = sorted(
            (v.priority for v in self.processor.validators),
            reverse=True
        )
        descending_priorities: list[int] = sorted(set(all_priorities), reverse=True)

        validation_info: str = (
            "Validators by priority (lower number means a higher priority):\n\n"
        )
        for priority in descending_priorities:
            validation_info += (
                f"Priority {priority}:\n"
                f"{_get_validators_info(
                    self.processor.validators_with_priority(priority)
                )}\n"
            )
            validation_info += "\n"

        return validation_info.strip()

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
                    "content": VALIDATOR_PROMPT
                },
                {
                    "role": "user",
                    "content": (
                        f"Validations:\n\n{self.extract_validation_info()}\n\n"
                        f"Leads:\n\n{CSVStringFormatter().deliver(pii_md5s)}"
                    )
                }
            ],
            max_tokens=4095,
            temperature=1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format=ValidatedLeadInsights
        )

        lead_insights: ValidatedLeadInsights | None = result.choices[0].message.parsed

        if not lead_insights:
            return "No insights on these leads at the moment."

        # Process insights to create an ordered list
        processed_insights: list[str] = []
        for i, insight in enumerate(lead_insights.insights, start=1):
            processed_insights.append(f"{i}. {insight}")

        total_str: str = "\n".join(processed_insights)

        # Insert validation message at the start
        if lead_insights.validation_insight:
            total_str = f"On validation: {lead_insights.validation_insight}\n\n{total_str}"

        return total_str
