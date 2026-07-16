import os
from sqlalchemy import text

from db import get_engine
from extract import extract
from transform import transform
from load import load


def main():
    engine = get_engine()

    # Locate the CSV file (assuming it's in data/raw/ relative to project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(project_root, "data", "raw", "candidates(1).csv")

    # Extract
    df = extract(csv_path)

    # Transform: returns 6 objects (5 dims + fact_stage)
    dim_candidate, dim_date, dim_location, dim_technology, dim_seniority, fact_stage = transform(df)

    # Load into Data Warehouse
    load(
        engine=engine,
        dim_candidate=dim_candidate,
        dim_date=dim_date,
        dim_location=dim_location,
        dim_technology=dim_technology,
        dim_seniority=dim_seniority,
        fact_stage=fact_stage,
        reset=True
    )

    # Quick verification: count rows in each table
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM dim_candidate) AS dim_candidate,
                (SELECT COUNT(*) FROM dim_date) AS dim_date,
                (SELECT COUNT(*) FROM dim_location) AS dim_location,
                (SELECT COUNT(*) FROM dim_technology) AS dim_technology,
                (SELECT COUNT(*) FROM dim_seniority) AS dim_seniority,
                (SELECT COUNT(*) FROM fact_application) AS fact_application;
        """)).mappings().first()

    print("✅ Row counts in Data Warehouse:")
    print(dict(res))


if __name__ == "__main__":
    main()