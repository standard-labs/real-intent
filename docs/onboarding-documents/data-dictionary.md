---
description: >-
  This document provides a detailed breakdown of Real Intent’s lead data,
  designed to help real estate professionals connect with motivated buyers and
  sellers. It covers intent-based categories, verifie
cover: >-
  https://wallpapers.com/images/hd/vibrant-purple-aura-abstract-q2k6xh20nl2jxckp.jpg
coverY: 0
---

# 📑 Data Dictionary

## Intent Categories

**Pre Mover**

Indicates visits to moving-related websites (e.g., U-Haul, Public Storage). Users have shown intent to move.

**Broker and Agent**

Represents visits to large brokerage websites (e.g., eXp Realty, Century 21), suggesting a user is seeking a real estate broker or agent.

**Educational Content for Real Estate**

Users visiting educational websites for first-time homebuyers or looking for information on mortgages (e.g., HELOC loans, FHA loans). Not necessarily first-time buyers but researching financing or housing options.

**Mortgage**

Visits to mortgage-related websites (e.g., Rocket Mortgage, LendingTree).

**Residential**

Represents visits to real estate listing websites (e.g., Zillow, Redfin), indicating intent to purchase property.

**Sellers**

Indicates visits to websites where users are searching for information on the value of their house, a sign of potential selling interest. This category is less frequent but very valuable.

{% hint style="info" %}
_Note:_

* _Each intent category is marked with an "**X**" in the Google Sheet if the individual has visited a related website, showing their interaction within that specific category._
* _For a user to be included in the data, they must have shown activity on at least two different occasions within the same category._
* _The data provided is no more than 7 days old at the time it is sent out, ensuring that the leads are fresh and relevant._
{% endhint %}



***

## Personal Information Columns

**First Name**

The individual's first name collected from the user data.

**Last Name**

The individual's last name.

**Emails** (Up to 3):

Email addresses collected based on the user’s activity online. All emails undergo SMTP validation to ensure they are active and valid.

{% hint style="info" %}
_If an email is absent, it is likely scrubbed due to **invalidity**._
{% endhint %}

**Phone Number** (Up to 3)

Phone numbers validated to ensure they are active and correct.

**Do Not Call List**

<mark style="background-color:green;">True</mark>: The number is on the Do Not Call List (cannot be contacted for cold calls).

<mark style="background-color:red;">False</mark>: The number is not on the Do Not Call List (safe to contact).



***

## Location Data

**Address**

Represents the residence of the individual.

**City, State, ZIP Code**

Basic geographical information to target leads by location.

**ZIP Code**

Useful for campaigns targeting specific ZIP codes.



***

## Demographic Information

**Gender**&#x20;

This field captures the gender of the individual, providing insight into household dynamics.

**Age**&#x20;

This field indicates the individual’s age, typically focusing on older demographics who are more likely to opt into data collections.

**Children**&#x20;

This binary data point indicates whether children are present in the household:

* **1** (<mark style="background-color:green;">Yes</mark>): There are children in the household.
* **0** (<mark style="background-color:red;">No</mark>): There are **no** children in the household. This data is crucial for targeting family-oriented properties or communities.



***

## Homeownership and Financial Information

**Homeowner Status**&#x20;

This field indicates whether the individual owns a home. It is particularly significant for identifying potential sellers, as homeowners may be considering selling their property, upgrading, or downsizing.

**Income Range**&#x20;

Provides a household income range, offering insights into the financial capacity of the individual. &#x20;

**Marital Status**&#x20;

Contains information on the individual’s marital status, indicating whether they are married or single.&#x20;

**Net Worth**&#x20;

This field provides an estimate of the individual’s net worth. It helps agents assess the financial stability and purchasing power of potential clients, allowing for more targeted and relevant service offerings.

**Occupation**&#x20;

Captures the individual’s current occupation, if available. This information can offer insights into the individual’s lifestyle and financial capacity, aiding agents in tailoring their approaches and property recommendations.



***

## MD5 Hash (Hashed Email)

This field contains a unique identifier for each individual, achieved through hashing their email address. This hashed email allows for targeted digital advertising, enabling agents to run campaigns specifically aimed at the individual’s household across connected devices (e.g., Amazon Fire, Google Chrome, Safari) or custom audience targeting on platforms like Facebook. By using the MD5 hash, agents can respect privacy while effectively reaching their target audience with personalized ads.
