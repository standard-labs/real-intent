"""Read the taxonomy."""
from pathlib import Path
import pandas as pd
            

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


def code_to_category(code: str | int) -> str:
    """Return the code for a given category."""
    df = pd.read_csv(Path(__file__).parent / 'iab_categories.csv')

    try:
        code = int(code)
    except ValueError:
        return code 

    # Search for the category
    result: pd.DataFrame = df[df["IAB_Category_ID"] == code]

    if result.empty:
        return code

    return result.iloc[0]["IAB_Category_Name"]
