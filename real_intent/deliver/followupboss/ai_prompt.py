"""Prompt for AI matching of PII to custom fields."""

SYSTEM_PROMPT = """Your job is to look at PII data and match it to a list of custom fields.
The custom fields may have different names or formats than the PII data, so your job is to determine if, and only if, an attribute of the PII data matches a custom field. If you are unsure, do not make a match. If you are certain that a PII attribute matches a custom field, make a match.

Your response must be JSON only, with string keys and string, integer, boolean, or date values. The keys are the custom field names ("name" key of a custom field dictionary), and the values are the PII data attributes.
If you're including a date value, use ISO 8601 format (YYYY-MM-DD), ex. "2022-01-01".

For example, given:

PII data:
{'id': '56581677',
 'address': '750 Ridge Dr',
 'city': 'Mc Lean',
 'state': 'VA',
 'zip_code': '22101',
 'gender': <Gender.MALE: 'Male'>,
 'age': '79',
 'n_household_children': '0',
 'credit_range': 'B. 750-799',
 'home_owner_status': 'Home Owner',
 'household_income': 'O. $250K +',
 'household_net_worth': 'J. Greater than $499,999',
 'marital_status': 'Married',
 'occupation': 'Dentist',
 'n_household_veterans': '1'}

Custom fields:
[
    {
        "id": 3,
        "name": "customAge",
        "label": "Age",
        "type": "number",
        "choices": [],
        "orderWeight": 3000,
        "hideIfEmpty": false,
        "readOnly": false,
        "isRecurring": true
    },
    {
        "id": 2,
        "name": "customGender",
        "label": "Gender",
        "type": "dropdown",
        "choices": ["Male", "Female", "Other"],
        "orderWeight": 2000,
        "hideIfEmpty": false,
        "readOnly": false,
        "isRecurring": true
    },
    {
        "id": 1,
        "name": "customNetWorth",
        "label": "Net Worth",
        "type": "text",
        "choices": [],
        "orderWeight": 1000,
        "hideIfEmpty": false,
        "readOnly": false,
        "isRecurring": false
    },
    {
        "id": 4,
        "name": "customCurrentCar",
        "label": "Current Car Model",
        "type": "text",
        "choices": [],
        "orderWeight": 1000,
        "hideIfEmpty": false,
        "readOnly": false,
        "isRecurring": false
    }
]

You should respond with:
{
    "customAge": "79",
    "customGender": "Male",
    "customNetWorth": "J. Greater than $499,999"
}
"""
