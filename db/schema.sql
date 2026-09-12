-- =========================================================
-- NIFTY 100 FINANCIAL DATABASE
-- Sprint 1 - Day 04
-- SQLite Database Schema
-- =========================================================


-- Enable Foreign Key Constraints
PRAGMA foreign_keys = ON;


-- =========================================================
-- DROP TABLES
-- Child tables must be dropped before parent tables
-- =========================================================

DROP TABLE IF EXISTS prosandcons;

DROP TABLE IF EXISTS documents;

DROP TABLE IF EXISTS analysis;

DROP TABLE IF EXISTS cashflow;

DROP TABLE IF EXISTS profitandloss;

DROP TABLE IF EXISTS balancesheet;

DROP TABLE IF EXISTS companies;


-- =========================================================
-- TABLE 1: COMPANIES
-- Parent Table
-- =========================================================

CREATE TABLE companies (

    id TEXT PRIMARY KEY,

    company_logo TEXT,

    company_name TEXT NOT NULL,

    chart_link TEXT,

    about_company TEXT,

    website TEXT,

    nse_profile TEXT,

    bse_profile TEXT,

    face_value REAL,

    book_value REAL,

    roce_percentage REAL,

    roe_percentage REAL
);


-- =========================================================
-- TABLE 2: ANALYSIS
-- =========================================================

CREATE TABLE analysis (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    compounded_sales_growth TEXT,

    compounded_profit_growth TEXT,

    stock_price_cagr TEXT,

    roe TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- =========================================================
-- TABLE 3: BALANCE SHEET
-- =========================================================

CREATE TABLE balancesheet (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    year INTEGER NOT NULL,

    equity_capital REAL,

    reserves REAL,

    borrowings REAL,

    other_liabilities REAL,

    total_liabilities REAL,

    fixed_assets REAL,

    cwip REAL,

    investments REAL,

    other_asset REAL,

    total_assets REAL,

    UNIQUE(company_id, year),

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- =========================================================
-- TABLE 4: CASH FLOW
-- =========================================================

CREATE TABLE cashflow (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    year INTEGER NOT NULL,

    operating_activity REAL,

    investing_activity REAL,

    financing_activity REAL,

    net_cash_flow REAL,

    UNIQUE(company_id, year),

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- =========================================================
-- TABLE 5: PROFIT AND LOSS
-- =========================================================

CREATE TABLE profitandloss (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    year INTEGER NOT NULL,

    sales REAL,

    expenses REAL,

    operating_profit REAL,

    opm_percentage REAL,

    other_income REAL,

    interest REAL,

    depreciation REAL,

    profit_before_tax REAL,

    tax_percentage REAL,

    net_profit REAL,

    eps REAL,

    dividend_payout REAL,

    UNIQUE(company_id, year),

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- =========================================================
-- TABLE 6: DOCUMENTS
-- =========================================================

CREATE TABLE documents (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    year INTEGER,

    annual_report TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- =========================================================
-- TABLE 7: PROS AND CONS
-- =========================================================

CREATE TABLE prosandcons (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    pros TEXT,

    cons TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- =========================================================
-- INDEXES
-- These improve query performance
-- =========================================================

CREATE INDEX idx_analysis_company
ON analysis(company_id);


CREATE INDEX idx_balancesheet_company
ON balancesheet(company_id);


CREATE INDEX idx_balancesheet_year
ON balancesheet(year);


CREATE INDEX idx_cashflow_company
ON cashflow(company_id);


CREATE INDEX idx_cashflow_year
ON cashflow(year);


CREATE INDEX idx_profitandloss_company
ON profitandloss(company_id);


CREATE INDEX idx_profitandloss_year
ON profitandloss(year);


CREATE INDEX idx_documents_company
ON documents(company_id);


CREATE INDEX idx_documents_year
ON documents(year);


CREATE INDEX idx_prosandcons_company
ON prosandcons(company_id);


-- =========================================================
-- END OF SCHEMA
-- =========================================================
