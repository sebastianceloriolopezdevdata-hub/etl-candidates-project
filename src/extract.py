import pandas as pd

def extract(csv_path: str) -> pd.DataFrame:
    """
    Extract:
    - Reads candidates.csv
    - Does minimal cleaning so Transform can rely on consistent columns
    """
    df = pd.read_csv(csv_path, sep=";")

    # strip + normalize
    for c in ["First Name", "Last Name", "Email", "Country", "Seniority", "Technology"]:
        df[c] = df[c].astype(str).str.strip()
    df["Email"] = df["Email"].str.lower()

    # types
    df["Application Date"] = pd.to_datetime(df["Application Date"], errors="coerce")
    if df["Application Date"].isna().any():
        bad = df[df["Application Date"].isna()].head(5)
        raise ValueError(f"Invalid Application Date values found. Examples:\n{bad}")

    for col in ["YOE", "Code Challenge Score", "Technical Interview Score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # text nulls
    for c in ["Country", "Seniority", "Technology"]:
        df[c] = df[c].replace({"": None, "nan": None}).fillna("Unknown")

    return df