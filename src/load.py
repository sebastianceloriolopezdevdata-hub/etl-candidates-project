from sqlalchemy import text

def _truncate_all(conn):
    """
    Truncate all tables and restart identity sequences.
    This ensures a clean state for each ETL run.
    """
    conn.execute(text("TRUNCATE TABLE fact_application RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE dim_candidate RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE dim_date RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE dim_location RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE dim_technology RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE dim_seniority RESTART IDENTITY CASCADE;"))


def load(engine, dim_candidate, dim_date, dim_location, 
         dim_technology, dim_seniority, fact_stage, reset=True):
    """
    Load:
    - Inserts dimensions (uses UNIQUE constraints + ON CONFLICT DO NOTHING)
    - Inserts fact by joining dimensions to get surrogate keys
    - Since we truncate fact_application each run, we don't need conflict handling on source_hash.
    
    Parameters:
    - engine: SQLAlchemy engine connected to PostgreSQL
    - dim_candidate: DataFrame with columns (first_name, last_name, email)
    - dim_date: DataFrame with columns (date_sk, full_date, year, month, day, quarter)
    - dim_location: DataFrame with columns (country)
    - dim_technology: DataFrame with columns (technology_name)
    - dim_seniority: DataFrame with columns (seniority_name)
    - fact_stage: DataFrame with natural keys + measures + source_hash
    - reset: If True, truncates all tables before loading
    """
    
    with engine.begin() as conn:
        if reset:
            print("🧹 Truncating tables...")
            _truncate_all(conn)

        # ---- DIM CANDIDATE ----
        print("📥 Loading dim_candidate...")
        dim_candidate[["first_name", "last_name", "email"]].to_sql(
            "tmp_dim_candidate", conn, if_exists="replace", index=False
        )
        conn.execute(text("""
            INSERT INTO dim_candidate (first_name, last_name, email)
            SELECT DISTINCT first_name, last_name, email
            FROM tmp_dim_candidate
            ON CONFLICT (email) DO NOTHING;
        """))

        # ---- DIM DATE (now includes date_sk) ----
        print("📥 Loading dim_date...")
        dim_date[["date_sk", "full_date", "year", "month", "day", "quarter"]].to_sql(
            "tmp_dim_date", conn, if_exists="replace", index=False
        )
        conn.execute(text("""
            INSERT INTO dim_date (date_sk, full_date, year, month, day, quarter)
            SELECT DISTINCT date_sk, full_date, year, month, day, quarter
            FROM tmp_dim_date
            ON CONFLICT (date_sk) DO NOTHING;   -- PK conflict
        """))

        # ---- DIM LOCATION ----
        print("📥 Loading dim_location...")
        dim_location[["country"]].to_sql(
            "tmp_dim_location", conn, if_exists="replace", index=False
        )
        conn.execute(text("""
            INSERT INTO dim_location (country)
            SELECT DISTINCT country
            FROM tmp_dim_location
            ON CONFLICT (country) DO NOTHING;
        """))

        # ---- DIM TECHNOLOGY ----
        print("📥 Loading dim_technology...")
        dim_technology[["technology_name"]].to_sql(
            "tmp_dim_technology", conn, if_exists="replace", index=False
        )
        conn.execute(text("""
            INSERT INTO dim_technology (technology_name)
            SELECT DISTINCT technology_name
            FROM tmp_dim_technology
            ON CONFLICT (technology_name) DO NOTHING;
        """))

        # ---- DIM SENIORITY ----
        print("📥 Loading dim_seniority...")
        dim_seniority[["seniority_name"]].to_sql(
            "tmp_dim_seniority", conn, if_exists="replace", index=False
        )
        conn.execute(text("""
            INSERT INTO dim_seniority (seniority_name)
            SELECT DISTINCT seniority_name
            FROM tmp_dim_seniority
            ON CONFLICT (seniority_name) DO NOTHING;
        """))

        # ---- FACT STAGE ----
        print("📥 Loading fact_stage (temporary table)...")
        fact_stage.to_sql("tmp_fact_stage", conn, if_exists="replace", index=False)

        # ---- INSERT FACT (resolve SKs via joins) ----
        # No ON CONFLICT because we TRUNCATE fact_application each run.
        print("📥 Inserting into fact_application (resolving surrogate keys)...")
        conn.execute(text("""
            INSERT INTO fact_application
              (candidate_sk, technology_sk, seniority_sk, date_sk, location_sk,
               yoe, code_challenge_score, technical_interview_score, is_hired)
            SELECT
              c.candidate_sk,
              t.technology_sk,
              s.seniority_sk,
              d.date_sk,
              l.location_sk,
              f.yoe,
              f.code_challenge_score,
              f.technical_interview_score,
              f.is_hired::int
            FROM tmp_fact_stage f
            JOIN dim_candidate c ON c.email = f.email
            JOIN dim_technology t ON t.technology_name = f.technology_name
            JOIN dim_seniority s ON s.seniority_name = f.seniority_name
            JOIN dim_date d ON d.full_date = f.full_date
            JOIN dim_location l ON l.country = f.country
        """))

    print("✅ Load complete.")