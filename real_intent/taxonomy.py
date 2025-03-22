"""Read the taxonomy."""
from pathlib import Path
import pandas as pd

from functools import lru_cache


# Read the taxonomy file
taxonomy_df = pd.read_csv(Path(__file__).parent / 'iab_categories.csv')


# This deprecated function used the old taxonomy.tsv file.
def _dep_old_code_to_category(code: str | int) -> str:
    """Return the category for a given code."""
    df = pd.read_csv(Path(__file__).parent / 'taxonomy.tsv', sep="\t")
    code = str(code)

    result: pd.DataFrame = df[df["Unique ID"] == code]
    if result.empty:
        return str(code)

    row = result.iloc[0]

    tiers: list[str] = []
    for i in range(1, 4+1):
        if not isinstance(row[f"Tier {i}"], str):
            break

        tiers.append(row[f"Tier {i}"])

    if not tiers:
        return row['Name']

    return f"{row['Name']}>{'>'.join(tiers)}"


@lru_cache(maxsize=None)
def code_to_category(code: str | int | None) -> str:
    """Return the category for a given code."""
    if code is None:
        return "None"

    try:
        code = int(code)
    except (ValueError, TypeError):
        return str(code)

    # Search for the category
    result: pd.DataFrame = taxonomy_df[taxonomy_df["IAB_Category_ID"] == code]

    if result.empty:
        return str(code)

    return str(result.iloc[0]["IAB_Category_Name"])


@lru_cache(maxsize=None)
def category_to_code(category: str) -> int | None:
    """Return the code for a given category."""
    result: pd.DataFrame = taxonomy_df[taxonomy_df["IAB_Category_Name"] == category]

    if result.empty:
        return None

    return int(result.iloc[0]["IAB_Category_ID"])
