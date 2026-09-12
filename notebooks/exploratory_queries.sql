-- =========================================================
-- SPRINT 1 - DAY 07
-- EXPLORATORY QUERIES
-- =========================================================


-- =========================================================
-- QUERY 01
-- TOTAL NUMBER OF COMPANIES
-- =========================================================

SELECT
    COUNT(*) AS total_companies
FROM companies;


-- =========================================================
-- QUERY 02
-- COMPANY MASTER LIST
-- =========================================================

SELECT
    id AS company_id,
    company_name,
    website,
    face_value,
    book_value,
    roce_percentage,
    roe_percentage
FROM companies
ORDER BY company_name;


-- =========================================================
-- QUERY 03
-- PROFIT AND LOSS YEAR COVERAGE
-- =========================================================

SELECT
    MIN(year) AS earliest_year,
    MAX(year) AS latest_year,
    COUNT(DISTINCT year) AS total_years
FROM profitandloss;


-- =========================================================
-- QUERY 04
-- COMPANY-WISE P&L COVERAGE
-- =========================================================

SELECT
    c.id AS company_id,
    c.company_name,
    MIN(p.year) AS earliest_year,
    MAX(p.year) AS latest_year,
    COUNT(DISTINCT p.year) AS year_count
FROM companies c
LEFT JOIN profitandloss p
    ON c.id = p.company_id
GROUP BY
    c.id,
    c.company_name
ORDER BY
    year_count DESC;


-- =========================================================
-- QUERY 05
-- TOP 10 COMPANIES BY LATEST NET PROFIT
-- =========================================================

SELECT
    c.company_name,
    p.year,
    p.net_profit
FROM profitandloss p
JOIN companies c
    ON p.company_id = c.id
WHERE p.year = (
    SELECT MAX(year)
    FROM profitandloss
)
ORDER BY
    p.net_profit DESC
LIMIT 10;


-- =========================================================
-- QUERY 06
-- TOP 10 COMPANIES BY ROE
-- =========================================================

SELECT
    id AS company_id,
    company_name,
    roe_percentage
FROM companies
WHERE roe_percentage IS NOT NULL
ORDER BY
    roe_percentage DESC
LIMIT 10;


-- =========================================================
-- QUERY 07
-- BALANCE SHEET CHECK
-- LIABILITIES VS ASSETS
-- =========================================================

SELECT
    company_id,
    year,
    total_liabilities,
    total_assets,
    ABS(
        total_liabilities - total_assets
    ) AS difference
FROM balancesheet
ORDER BY
    difference DESC
LIMIT 20;


-- =========================================================
-- QUERY 08
-- CASH FLOW ANALYSIS
-- =========================================================

SELECT
    c.company_name,
    cf.year,
    cf.operating_activity,
    cf.investing_activity,
    cf.financing_activity,
    cf.net_cash_flow
FROM cashflow cf
JOIN companies c
    ON cf.company_id = c.id
ORDER BY
    cf.net_cash_flow DESC
LIMIT 20;


-- =========================================================
-- QUERY 09
-- PROFITABILITY ANALYSIS
-- =========================================================

SELECT
    c.company_name,
    p.year,
    p.sales,
    p.operating_profit,
    p.opm_percentage,
    p.net_profit,
    p.eps
FROM profitandloss p
JOIN companies c
    ON p.company_id = c.id
ORDER BY
    p.net_profit DESC
LIMIT 20;


-- =========================================================
-- QUERY 10
-- COMPANIES WITH LESS THAN 5 YEARS OF P&L DATA
-- =========================================================

SELECT
    c.id AS company_id,
    c.company_name,
    COUNT(DISTINCT p.year) AS year_count
FROM companies c
LEFT JOIN profitandloss p
    ON c.id = p.company_id
GROUP BY
    c.id,
    c.company_name
HAVING
    COUNT(DISTINCT p.year) < 5
ORDER BY
    year_count;