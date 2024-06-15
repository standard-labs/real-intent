"""Read the taxonomy."""
from pathlib import Path
import pandas as pd
            

def code_to_category(code: str | int) -> str:
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
