-- =====================================================================
-- Workshop 1: Technology Recruitment Data Warehouse
-- Task 6: Analytical Queries & KPIs (PostgreSQL)
-- =====================================================================

-- ---------------------------------------------------------------------
-- R1 — Hiring Trends
-- Business Question: How has the number of hires varied over the years?
-- ---------------------------------------------------------------------
SELECT
    d.year,
    COUNT(f.application_sk) AS total_applications,
    SUM(f.is_hired) AS total_hires,
    ROUND(AVG(f.is_hired) * 100, 2) AS hire_rate_percentage
FROM fact_application f
JOIN dim_date d ON f.date_sk = d.date_sk
GROUP BY d.year
ORDER BY d.year;


-- ---------------------------------------------------------------------
-- R2 — Technology Analysis
-- Business Question: Which technologies have the highest hiring rate?
-- ---------------------------------------------------------------------
SELECT
    t.technology_name,
    COUNT(f.application_sk) AS total_applications,
    SUM(f.is_hired) AS total_hires,
    ROUND(AVG(f.is_hired) * 100, 2) AS hire_rate_percentage
FROM fact_application f
JOIN dim_technology t ON f.technology_sk = t.technology_sk
GROUP BY t.technology_name
ORDER BY hire_rate_percentage DESC;


-- ---------------------------------------------------------------------
-- R3 — Candidate Profile Analysis
-- Business Question: How do seniority and YOE influence hiring?
-- ---------------------------------------------------------------------
SELECT
    s.seniority_name,
    COUNT(f.application_sk) AS total_applications,
    ROUND(AVG(f.yoe), 1) AS avg_years_of_experience,
    SUM(f.is_hired) AS total_hires,
    ROUND(AVG(f.is_hired) * 100, 2) AS hire_rate_percentage
FROM fact_application f
JOIN dim_seniority s ON f.seniority_sk = s.seniority_sk
GROUP BY s.seniority_name
ORDER BY hire_rate_percentage DESC;


-- ---------------------------------------------------------------------
-- R4 — Geographic Efficiency Analysis
-- Business Question: In which countries are we most efficient at hiring?
-- ---------------------------------------------------------------------
SELECT
    l.country,
    COUNT(f.application_sk) AS total_applications,
    SUM(f.is_hired) AS total_hires,
    ROUND(AVG(f.is_hired) * 100, 2) AS hire_rate_percentage
FROM fact_application f
JOIN dim_location l ON f.location_sk = l.location_sk
GROUP BY l.country
ORDER BY total_applications DESC;


-- ---------------------------------------------------------------------
-- R5 — Seniority Gap Analysis by Technology
-- Business Question: Which seniority level is hired most per technology?
-- ---------------------------------------------------------------------
SELECT
    t.technology_name,
    s.seniority_name,
    COUNT(f.application_sk) AS total_hires
FROM fact_application f
JOIN dim_technology t ON f.technology_sk = t.technology_sk
JOIN dim_seniority s ON f.seniority_sk = s.seniority_sk
WHERE f.is_hired = 1
GROUP BY t.technology_name, s.seniority_name
ORDER BY t.technology_name, total_hires DESC;