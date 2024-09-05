"""Datatypes for working with the API."""
from pydantic import BaseModel, Field, field_validator, model_validator

from typing import Any, Self
from enum import Enum

from real_intent.taxonomy import code_to_category


class ConfigDates(BaseModel):
    """Start and end dates as returned by the /config route."""
    start_date: str
    end_date: str


class IABJob(BaseModel):
    """Payload for creating an IAB job."""
    intent_categories: list[str] = Field(
        default_factory=list, description="List of IAB intent categories"
    )
    zips: list[str] = Field(
        default_factory=list, description="List of zip codes"
    )
    keywords: list[str] = Field(
        default_factory=list, description="List of keywords"
    )
    domains: list[str] = Field(
        default_factory=list, description="List of domains"
    )
    n_hems: int

    @model_validator(mode="after")
    def validate_job(self) -> Self:
        """Make sure the job has enough information to run."""
        if all(
            [
                not self.intent_categories,
                not self.keywords,
                not self.domains
            ]
        ):
            raise ValueError(
                "Need at least one of intent categories, keywords, or domains.\n" + str(self.model_dump())
            )

        return self

    def as_payload(self) -> dict[str, str]:
        """Convert into dictionary payload."""
        return {
            "IABs": ",".join(self.intent_categories),
            "Zips": ",".join(self.zips),
            "Keywords": ",".join(self.keywords),
            "Domains": ",".join(self.domains),
            "NumberOfHems": self.n_hems
        }


class IntentEvent(BaseModel):
    """
    MD5 intent event as returned by API.
    Timestamp not supported yet.
    """
    md5: str
    sentence: str


class UniqueMD5(BaseModel):
    """
    Unique MD5 with all the associated sentences.

    `sentences` should be defined as whatever comes back from the API.
    Field validation automatically transforms IAB _codes_ into _strings_
    and removes duplicates.
    """
    md5: str
    sentences: list[str]

    @field_validator("sentences", mode="after")
    def transform_iab_codes(sentences: list[str]) -> list[str]:
        """Convert any valid IAB codes into strings."""
        sentences = list(set(sentences))

        for pos, sentence in enumerate(sentences):
            if sentence.isnumeric():
                sentences[pos] = code_to_category(sentence)

        return sentences
    

class MobilePhone(BaseModel):
    """An individual's phone number."""
    phone: str
    do_not_call: bool


class Gender(str, Enum):
    """Classifications of genders."""
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown"
    EMPTY = ""


class PII(BaseModel):
    """
    PII in output code 10026 as returned by BigDBM API directly.
    No transformations, only typed data validation.

    Instantiate with `.from_api_dict` to ensure correct pre-processing of 
    mobile phone data.
    """
    id: str = Field(..., alias="Id", description="BigDBM person ID")
    first_name: str = Field(..., alias="First_Name")
    last_name: str = Field(..., alias="Last_Name")
    address: str = Field(..., alias="Address")
    city: str = Field(..., alias="City")
    # national_consumer_database  # what is this, and what type?
    state: str = Field(..., alias="State")
    zip_code: str = Field(..., alias="Zip")
    zip4: str = Field(..., alias="Zip4")
    fips_state_code: str = Field(..., alias="Fips_State_Code")
    fips_county_code: str = Field(..., alias="Fips_County_Code")
    county_name: str = Field(..., alias="County_Name")
    latitude: float = Field(..., alias="Latitude")
    longitude: float = Field(..., alias="Longitude")
    address_type: str = Field(..., alias="Address_Type")
    cbsa: str = Field(..., alias="Cbsa")
    census_tract: str = Field(..., alias="Census_Tract")
    census_block_group: int = Field(..., alias="Census_Block_Group")
    census_block: str = Field(..., alias="Census_Block")
    gender: Gender = Field(..., alias="Gender")
    scf: str = Field(..., alias="SCF")
    dma: str = Field(..., alias="DMA")
    msa: str = Field(..., alias="MSA")
    congressional_district: str = Field(..., alias="Congressional_District")
    head_of_household: bool = Field(..., alias="HeadOfHousehold")
    birth_month_and_year: str = Field(..., alias="Birth_Month_and_Year")
    age: int = Field(..., alias="Age")
    prop_type: str = Field(..., alias="Prop_Type")
    emails: list[str] = Field(..., alias="Email_Array")
    mobile_phones: list[MobilePhone] = []
    n_household_children: int = Field(..., alias="Children_HH", description="String number of children in the household")
    credit_range: str = Field(..., alias="Credit_Range")
    household_income: str = Field(..., alias="Income_HH", description="Descriptor of household income")
    household_net_worth: str = Field(..., alias="Net_Worth_HH", description="Descriptor of household net worth")
    home_owner_status: str = Field(
        ..., alias="Home_Owner", description="Descriptor of home ownership status"
    )
    marital_status: str = Field(..., alias="Marital_Status", description="Descriptor of marital status")
    occupation: str = Field(..., alias="Occupation_Detail")
    median_home_value: int = Field(..., alias="Median_Home_Value")
    education: str = Field(..., alias="Education")
    length_of_residence: int = Field(..., alias="Length_of_Residence")
    n_household_adults: int = Field(..., alias="Num_Adults_HH", description="String number of adults in the household")
    political_party: str = Field(..., alias="Political_Party")
    health_beauty_products: bool = Field(..., alias="Health_Beauty_Products")
    cosmetics: bool = Field(..., alias="Cosmetics")
    jewelry: bool = Field(..., alias="Jewelry")
    investment_type: bool = Field(..., alias="Investment_Type")
    investments: bool = Field(..., alias="Investments")
    pet_owner: bool = Field(..., alias="Pet_Owner")
    pets_affinity: bool = Field(..., alias="Pets_Affinity")
    health_affinity: bool = Field(..., alias="Health_Affinity")
    diet_affinity: bool = Field(..., alias="Diet_Affinity")
    fitness_affinity: bool = Field(..., alias="Fitness_Affinity")
    outdoors_affinity: bool = Field(..., alias="Outdoors_Affinity")
    boating_sailing_affinity: bool = Field(..., alias="Boating_Sailing_Affinity")
    camping_hiking_climbing_affinity: bool = Field(..., alias="Camping_Hiking_Climbing_Affinity")
    fishing_affinity: bool = Field(..., alias="Fishing_Affinity")
    hunting_affinity: bool = Field(..., alias="Hunting_Affinity")
    aerobics: bool = Field(..., alias="Aerobics")
    nascar: bool = Field(..., alias="NASCAR")
    scuba: bool = Field(..., alias="Scuba")
    weight_lifting: bool = Field(..., alias="Weight_Lifting")
    healthy_living_interest: bool = Field(..., alias="Healthy_Living_Interest")
    motor_racing: bool = Field(..., alias="Motor_Racing")
    foreign_travel: bool = Field(..., alias="Travel_Foreign")
    self_improvement: bool = Field(..., alias="Self_Improvement")
    walking: bool = Field(..., alias="Walking")
    fitness: bool = Field(..., alias="Fitness")
    ethnicity_detail: str = Field(..., alias="Ethnicity_Detail")
    ethnic_group: str = Field(..., alias="Ethnic_Group")

    def hash(self: "PII") -> str:
        """Hash with instance attributes."""
        return f"{self.first_name} {self.last_name} {self.zip_code} {self.age} {self.household_net_worth} {self.household_income}"

    def __eq__(self, other: "PII") -> bool:
        """Approximate if two PII objects are equivalent based on attributes."""
        if not isinstance(other, PII):
            raise TypeError(f"Cannot compare PII with {type(other)}.")

        return self.hash() == other.hash()

    @classmethod
    def from_api_dict(cls, api_dict: dict[str, Any]) -> Self:
        """Read in the data and parse the mobile phones and gender."""
        mobile_phones: list[MobilePhone] = []
        for i in range(1, 3+1):
            if f"Mobile_Phone_{i}" in api_dict:
                phone: str = api_dict[f"Mobile_Phone_{i}"]

                if not phone:
                    continue

                dnc: bool = True if api_dict[f"Mobile_Phone_{i}_DNC"] == "1" else False
                mobile_phones.append(MobilePhone(phone=phone, do_not_call=dnc))

        if not api_dict["Email_Array"]:
            api_dict["Email_Array"] = []

        # Gender is returned as "M" or "F" in the 10026 API output
        if api_dict.get('Gender') == 'M':
            api_dict['Gender'] = 'Male'
        elif api_dict.get('Gender') == 'F':
            api_dict['Gender'] = 'Female'
        else:
            api_dict['Gender'] = 'Unknown'

        return cls(**api_dict, mobile_phones=mobile_phones)

    def as_lead_export(self) -> dict[str, Any]:
        """
        Dictionary output ready for insertion into a lead export.
        Emails and phone numbers are separated into unique attributes.
        """
        export_dict: dict[str, Any] = self.model_dump()

        # Remove unwanted fields
        if "id" in export_dict:
            del export_dict["id"]

        if "national_consumer_database" in export_dict:
            del export_dict["national_consumer_database"]

        # Separate Emails
        export_dict["email_1"] = None
        export_dict["email_2"] = None
        export_dict["email_3"] = None

        for pos, email in enumerate(self.emails[:3], start=1):
            export_dict[f"email_{pos}"] = email
    
        del export_dict["emails"]

        # Separate phone numbers
        export_dict["phone_1"] = None
        export_dict["phone_1_dnc"] = None
        export_dict["phone_2"] = None
        export_dict["phone_2_dnc"] = None
        export_dict["phone_3"] = None
        export_dict["phone_3_dnc"] = None

        phone: MobilePhone
        for pos, phone in enumerate(self.mobile_phones, start=1):
            export_dict[f"phone_{pos}"] = phone.phone
            export_dict[f"phone_{pos}_dnc"] = phone.do_not_call
        
        del export_dict["mobile_phones"]

        # Convert gender to string
        export_dict["gender"] = export_dict["gender"].value

        return export_dict


class MD5WithPII(UniqueMD5):
    """
    A unique MD5 with several sentences but also including an attribute with
    a dictionary of PII data returned directly by the API.

    Note: In the future, instead of housing a top-level `pii` attribute, 
    encode each PII attribute with the appropriate data type for full model
    validation.
    """
    pii: PII

    def hash(self: "MD5WithPII") -> str:
        """Hash with PII instance attritutes."""
        return self.pii.hash()

    def __eq__(self, other: "MD5WithPII") -> bool:
        """Approximate if two MD5WithPII objects are equivalent based on PII."""
        if not isinstance(other, MD5WithPII):
            raise TypeError(f"Cannot compare MD5WithPII with {type(other)}.")

        return self.hash() == other.hash()
