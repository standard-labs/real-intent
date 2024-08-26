"""Base processor."""
from abc import ABC, abstractmethod
from typing import Self, NamedTuple

from bigdbm.client import BigDBMClient
from bigdbm.schemas import IABJob, MD5WithPII
from bigdbm.validate.base import BaseValidator
from bigdbm.validate.simple import ContactableValidator
from bigdbm.internal_logging import log, log_span


class ProcessValidator(NamedTuple):
    """
    Tuple for a validator used inside of a processor. 

    Has the `Validator` object in element 0 and an `int` priority
    in element 1. Both should always be provided on instantiation.
    """
    validator: BaseValidator
    priority: int


DEFAULT_VALIDATORS: list[BaseValidator] = [
    ContactableValidator()
]


class BaseProcessor(ABC):
    """
    Base processor, takes an IAB job and finishes with a list of MD5s with PII.
    All implementations must follow the `.process()` schema.

    The MD5s with PII are the input for deliverers.

    Comes with an __init__ that takes a BigDBM client. If overriding the __init__
    for some reason, be sure to super() and make sure self.client is defined.

    When working with validators, method chaining is possible as an instance of self
    is returned for `.add_validator` and `.clear_validators`.
    Ex: `FillProcessor(client).add_validator(validator).process(job)`
    """

    def __init__(self, bigdbm_client: BigDBMClient) -> None:
        """Initialize with a client."""
        self.client = bigdbm_client
        self.validators: list[ProcessValidator] = []

    @property
    def raw_validators(self) -> list[BaseValidator]:
        """
        A list of all raw `Validator` objects used without any priority info.
        This really shouldn't be used - `self.validators` is better. But this exists
        for backwards compatibility.
        """
        return [v.validator for v in self.validators]

    def clear_validators(self) -> Self:
        """Remove all validators from the processor."""
        self.validators = []
        return self

    def add_validator(self, validator: BaseValidator, priority: int = 1) -> Self:
        """
        Add a validator instance to the processor's validators.

        Args:
            validator: A BaseValidator instance.
            priority: A number, min of 1, indicating the priority level of the
                validator. 1 is the highest priority. Assuming the processor
                implements this behavior, it will iteratively remove validators
                from highest to lowest priority until the lead quota is filled. 
                As 1 is the lowest number and the highest priority, priority 1
                validators will never be removed - if leads do not pass priority 1
                validation, they can't possibly be returned.
        """
        if not isinstance(validator, BaseValidator):
            raise TypeError("You must pass in a valid BaseValidator instance.")

        # Check for valid priority
        if not isinstance(priority, int):
            raise TypeError("You must provide the priority as an integer.")

        if priority < 1:
            raise ValueError("Priority must be a minimum of 1 (highest priority).")

        self.validators.append(
            ProcessValidator(
                validator=validator,
                priority=priority
            )
        )

        return self

    @property
    def lowest_validation_priority(self) -> int:
        """
        Get the lowest priority of all validators.
        Note that this is the _highest_ integer, but semantically, the lowest
        priority as priority 1 is the highest priority (required).

        Returns 0 if there are no validators.
        """
        if not self.validators:
            return 0

        return max(self.validators, key=lambda v: v.priority).priority

    def validators_with_priority(self, priority: int) -> list[BaseValidator]:
        """
        Get all validators with a certain priority level. If there are none, an empty
        list is returned.
        """
        if not isinstance(priority, int):
            raise TypeError("You must provide the priority as an integer.")
        
        return [v.validator for v in self.validators if v.priority == priority]

    def min_priority_validators(self, priority: int) -> list[BaseValidator]:
        """
        Returns validators with priority at or above the given level (numerically, lower or equal).
        """
        if not isinstance(priority, int):
            raise TypeError("You must provide the priority as an integer.")
        
        if priority < 1:
            raise ValueError("Priority must be a minimum of 1 (highest priority).")
        
        return [v.validator for v in self.validators if v.priority <= priority]

    def add_default_validators(self, priority: int = 1) -> Self:
        """
        Insert the default validators into the processor. Note that these default 
        validators are added to the _end_ of the validators list, in case order of 
        validation matters (as it would when validating valid emails and has emails, 
        for example).

        Args:
            priority (int, optional): The priority to attach to default validators when
            added to the list. Defaults to 1 - highest priority, i.e. required.
        """
        # Ensure valid priority
        if not isinstance(priority, int):
            raise TypeError("You must provide the priority as an integer.")
        
        if priority < 1:
            raise ValueError("Priority must be a minimum of 1 (highest priority).")

        for validator in DEFAULT_VALIDATORS:
            self.add_validator(validator, priority=priority)

        return self

    def process(self, iab_job: IABJob) -> list[MD5WithPII]:
        """
        Take an IAB job and process it into a list of MD5s with PII.
        This method wraps the _process method with logging.
        """
        with log_span(f"Processing IAB job with {self.__class__.__name__}", _level="debug"):
            log("debug", f"Starting processing with {self.__class__.__name__}")
            result = self._process(iab_job)
            log("debug", f"Processing completed with {self.__class__.__name__}, generated {len(result)} MD5s with PII")
            return result

    @abstractmethod
    def _process(self, iab_job: IABJob) -> list[MD5WithPII]:
        """
        Internal method to be implemented by subclasses to perform the actual processing.
        """
        pass
