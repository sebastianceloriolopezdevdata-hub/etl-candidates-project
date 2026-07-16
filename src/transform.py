import hashlib
import pandas as pd

HIRED_THRESHOLD = 7

def _hash_row(values) -> str:
    """Generates a unique MD5 hash to detect changes or duplicates."""
    s = "|".join("" if v is None else str(v) for v in values)
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def transform(df: pd.DataFrame):
    """
    Transform adapted to the Star Schema (project DDL):
    - Generates separate dimensions (candidate, date, location, technology, seniority).
    - Generates fact_stage with Natural Keys + source_hash.
    - Surrogate Keys (SKs) will be resolved during the Load phase via SQL joins.
    """
    df = df.copy()

    # --- 1. Business rule: HIRED ---
    df["is_hired"] = ((df["Code Challenge Score"] >= HIRED_THRESHOLD) & 
                      (df["Technical Interview Score"] >= HIRED_THRESHOLD))

    # --- 2. Dimensions (NO Surrogate Keys, only business attributes) ---
    
    # Candidate Dimension (unique email)
    dim_candidate = (
        df[["First Name", "Last Name", "Email"]]
        .drop_duplicates(subset=["Email"])  # Ensure uniqueness on email
        .rename(columns={"First Name": "first_name", "Last Name": "last_name", "Email": "email"})
        .reset_index(drop=True)
    )

    # Date Dimension (includes Quarter as required by DDL)
    # Generate date_sk as integer YYYYMMDD (Primary Key)
    dim_date = (
        pd.DataFrame({"full_date": df["Application Date"].dt.date})
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_date["year"] = pd.to_datetime(dim_date["full_date"]).dt.year
    dim_date["month"] = pd.to_datetime(dim_date["full_date"]).dt.month
    dim_date["day"] = pd.to_datetime(dim_date["full_date"]).dt.day
    dim_date["quarter"] = pd.to_datetime(dim_date["full_date"]).dt.quarter
    # Create the surrogate key: integer in YYYYMMDD format (e.g., 20211005)
    dim_date["date_sk"] = pd.to_datetime(dim_date["full_date"]).dt.strftime('%Y%m%d').astype(int)
    # Reorder columns to match DDL (date_sk first)
    dim_date = dim_date[["date_sk", "full_date", "year", "month", "day", "quarter"]]

    # Location Dimension (unique country)
    dim_location = (
        df[["Country"]]
        .drop_duplicates()
        .rename(columns={"Country": "country"})
        .reset_index(drop=True)
    )

    # Technology Dimension (separated)
    dim_technology = (
        df[["Technology"]]
        .drop_duplicates()
        .rename(columns={"Technology": "technology_name"})
        .reset_index(drop=True)
    )

    # Seniority Dimension (separated)
    dim_seniority = (
        df[["Seniority"]]
        .drop_duplicates()
        .rename(columns={"Seniority": "seniority_name"})
        .reset_index(drop=True)
    )

    # --- 3. Fact Table Staging (Natural Keys + Hash) ---
    # Grain = 1 row per CSV record (50k rows)
    fact_stage = pd.DataFrame({
        "email": df["Email"].astype(str),
        "full_date": df["Application Date"].dt.date,
        "country": df["Country"].astype(str),
        "technology_name": df["Technology"].astype(str),
        "seniority_name": df["Seniority"].astype(str),
        "yoe": df["YOE"].astype(int),
        "code_challenge_score": df["Code Challenge Score"].astype(int),
        "technical_interview_score": df["Technical Interview Score"].astype(int),
        "is_hired": df["is_hired"].astype(bool),
    })

    # Generate hash for each fact row to avoid duplicates in future loads (CDC)
    fact_stage["source_hash"] = fact_stage.apply(
        lambda r: _hash_row([
            r["email"], r["full_date"], r["country"],
            r["technology_name"], r["seniority_name"],
            r["yoe"], r["code_challenge_score"], r["technical_interview_score"],
        ]),
        axis=1
    )

    # Integrity check: 1 row in fact_stage = 1 row in CSV
    if len(fact_stage) != len(df):
        raise ValueError("Grain violation: fact_stage must have 1 row per CSV record.")

    # Return the 5 dimensions + fact staging table
    return (dim_candidate, dim_date, dim_location, 
            dim_technology, dim_seniority, fact_stage)