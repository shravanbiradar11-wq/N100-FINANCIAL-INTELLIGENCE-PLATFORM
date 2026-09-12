from pathlib import Path
import sqlite3
from datetime import datetime

import pandas as pd


class DatabaseLoader:
    """
    Handles SQLite database creation, schema initialization,
    data loading, auditing and database integrity checks.

    IMPORTANT:
    - Foreign keys remain enabled.
    - This class does not silently disable constraints.
    - Source-row filtering/rejection should happen in run_day5_load.py
      before load_dataframe() is called.
    """

    def __init__(
        self,
        database_path="db/nifty100.db",
        schema_path="db/schema.sql"
    ):

        self.database_path = Path(database_path)
        self.schema_path = Path(schema_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.audit_records = []

    # =========================================================
    # DATABASE CONNECTION
    # =========================================================

    def get_connection(self):

        connection = sqlite3.connect(
            self.database_path
        )

        # ALWAYS enforce FK constraints.
        connection.execute(
            "PRAGMA foreign_keys = ON;"
        )

        return connection

    # =========================================================
    # CREATE DATABASE FROM SCHEMA
    # =========================================================

    def create_database(self, reset=False):
        """
        Create the SQLite database from schema.sql.

        reset=True removes the previous database before creating it.
        This is useful for Day 05 because a previous partially
        completed load must not remain in the database.
        """

        if not self.schema_path.exists():

            raise FileNotFoundError(
                f"Schema file not found: "
                f"{self.schema_path}"
            )

        print("\n" + "=" * 70)
        print("CREATING SQLITE DATABASE")
        print("=" * 70)

        # -----------------------------------------------------
        # RESET OLD DATABASE
        # -----------------------------------------------------

        if reset and self.database_path.exists():

            print(
                f"Removing existing database: "
                f"{self.database_path}"
            )

            self.database_path.unlink()

        with open(
            self.schema_path,
            "r",
            encoding="utf-8"
        ) as file:

            schema_sql = file.read()

        connection = self.get_connection()

        try:

            connection.executescript(
                schema_sql
            )

            connection.commit()

            print(
                "✓ Schema executed successfully."
            )

            # Verify FK enforcement.
            cursor = connection.cursor()

            cursor.execute(
                "PRAGMA foreign_keys;"
            )

            fk_enabled = cursor.fetchone()[0]

            if fk_enabled != 1:

                raise RuntimeError(
                    "SQLite foreign-key enforcement "
                    "could not be enabled."
                )

            print(
                "✓ Foreign-key enforcement enabled."
            )

        except sqlite3.Error as error:

            connection.rollback()

            print(
                f"✗ Database creation failed: "
                f"{error}"
            )

            raise

        finally:

            connection.close()

    # =========================================================
    # LOAD DATAFRAME INTO TABLE
    # =========================================================

    def load_dataframe(
        self,
        df,
        table_name,
        if_exists="append"
    ):
        """
        Load a validated DataFrame into SQLite.

        This method intentionally does NOT remove invalid rows.
        Data-quality filtering must be completed by the Day 05
        loading script before this method is called.

        If SQLite rejects the batch, the complete transaction is
        rolled back.
        """

        if df is None:

            raise ValueError(
                f"{table_name}: DataFrame is None."
            )

        rows_received = len(df)

        print("\n" + "-" * 70)
        print(
            f"LOADING TABLE: {table_name}"
        )
        print("-" * 70)

        print(
            f"Rows received: {rows_received}"
        )

        # -----------------------------------------------------
        # EMPTY DATAFRAME
        # -----------------------------------------------------

        if df.empty:

            self.audit_records.append({

                "timestamp":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "table_name":
                    table_name,

                "rows_received":
                    rows_received,

                "rows_loaded":
                    0,

                "rows_rejected":
                    rows_received,

                "status":
                    "SKIPPED_EMPTY"

            })

            print(
                "⚠ DataFrame is empty. Skipping."
            )

            return 0

        connection = self.get_connection()

        rows_loaded = 0
        rows_rejected = 0
        status = "SUCCESS"

        try:

            # -------------------------------------------------
            # SQLITE INSERT
            # -------------------------------------------------

            df.to_sql(
                name=table_name,
                con=connection,
                if_exists=if_exists,
                index=False,
                method="multi"
            )

            connection.commit()

            rows_loaded = len(df)

            rows_rejected = 0

            status = "SUCCESS"

            print(
                f"✓ Rows loaded: "
                f"{rows_loaded}"
            )

        except Exception as error:

            # IMPORTANT:
            # Roll back the complete batch.
            connection.rollback()

            rows_loaded = 0

            rows_rejected = rows_received

            status = "FAILED"

            print(
                f"✗ Loading failed: "
                f"{error}"
            )

            # Record the failed batch before raising.
            self.audit_records.append({

                "timestamp":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "table_name":
                    table_name,

                "rows_received":
                    rows_received,

                "rows_loaded":
                    rows_loaded,

                "rows_rejected":
                    rows_rejected,

                "status":
                    status

            })

            raise

        finally:

            connection.close()

        # -----------------------------------------------------
        # AUDIT RECORD
        # -----------------------------------------------------

        self.audit_records.append({

            "timestamp":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "table_name":
                table_name,

            "rows_received":
                rows_received,

            "rows_loaded":
                rows_loaded,

            "rows_rejected":
                rows_rejected,

            "status":
                status

        })

        return rows_loaded

    # =========================================================
    # GET TABLE ROW COUNT
    # =========================================================

    def get_row_count(
        self,
        table_name
    ):

        connection = self.get_connection()

        try:

            cursor = connection.cursor()

            query = (
                f"SELECT COUNT(*) "
                f"FROM {table_name};"
            )

            cursor.execute(query)

            count = cursor.fetchone()[0]

            return count

        finally:

            connection.close()

    # =========================================================
    # GET ALL TABLES
    # =========================================================

    def get_tables(self):

        connection = self.get_connection()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name;
                """
            )

            tables = [
                row[0]
                for row in cursor.fetchall()
            ]

            return tables

        finally:

            connection.close()

    # =========================================================
    # VERIFY FOREIGN KEYS ENABLED
    # =========================================================

    def verify_foreign_keys(self):

        connection = self.get_connection()

        try:

            cursor = connection.cursor()

            cursor.execute(
                "PRAGMA foreign_keys;"
            )

            result = cursor.fetchone()

            return result[0] == 1

        finally:

            connection.close()

    # =========================================================
    # CHECK FOREIGN KEY VIOLATIONS
    # =========================================================

    def foreign_key_check(self):

        connection = self.get_connection()

        try:

            cursor = connection.cursor()

            cursor.execute(
                "PRAGMA foreign_key_check;"
            )

            violations = cursor.fetchall()

            return violations

        finally:

            connection.close()

    # =========================================================
    # CHECK NULL YEARS
    # =========================================================

    def null_year_check(self):

        """
        Check all tables that require a non-null year.
        """

        tables = [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "documents"
        ]

        results = {}

        connection = self.get_connection()

        try:

            cursor = connection.cursor()

            existing_tables = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table';
                    """
                ).fetchall()
            }

            for table in tables:

                if table not in existing_tables:
                    continue

                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {table}
                    WHERE year IS NULL;
                    """
                )

                results[table] = cursor.fetchone()[0]

            return results

        finally:

            connection.close()

    # =========================================================
    # CHECK DUPLICATE COMPANY/YEAR GROUPS
    # =========================================================

    def duplicate_company_year_check(self):

        """
        Check tables where (company_id, year) must be unique.
        """

        tables = [
            "profitandloss",
            "balancesheet",
            "cashflow"
        ]

        results = {}

        connection = self.get_connection()

        try:

            cursor = connection.cursor()

            existing_tables = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table';
                    """
                ).fetchall()
            }

            for table in tables:

                if table not in existing_tables:
                    continue

                cursor.execute(
                    f"""
                    SELECT
                        company_id,
                        year,
                        COUNT(*) AS row_count
                    FROM {table}
                    GROUP BY company_id, year
                    HAVING COUNT(*) > 1;
                    """
                )

                results[table] = cursor.fetchall()

            return results

        finally:

            connection.close()

    # =========================================================
    # SAVE LOAD AUDIT
    # =========================================================

    def save_audit(
        self,
        output_path="output/load_audit.csv"
    ):

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        audit_df = pd.DataFrame(
            self.audit_records,
            columns=[
                "timestamp",
                "table_name",
                "rows_received",
                "rows_loaded",
                "rows_rejected",
                "status"
            ]
        )

        audit_df.to_csv(
            output_path,
            index=False
        )

        print("\n" + "=" * 70)
        print("LOAD AUDIT SAVED")
        print("=" * 70)

        print(
            f"Output: {output_path}"
        )

        return audit_df

    # =========================================================
    # VERIFY AUDIT RECONCILIATION
    # =========================================================

    def verify_audit_reconciliation(self):

        """
        Verify:

            rows_received =
            rows_loaded + rows_rejected

        for every audit record.
        """

        failures = []

        for record in self.audit_records:

            received = int(
                record["rows_received"]
            )

            loaded = int(
                record["rows_loaded"]
            )

            rejected = int(
                record["rows_rejected"]
            )

            if received != loaded + rejected:

                failures.append({
                    "table_name":
                        record["table_name"],

                    "rows_received":
                        received,

                    "rows_loaded":
                        loaded,

                    "rows_rejected":
                        rejected
                })

        return failures

    # =========================================================
    # PRINT DATABASE SUMMARY
    # =========================================================

    def print_database_summary(self):

        tables = self.get_tables()

        print("\n" + "=" * 70)
        print("DATABASE ROW COUNT SUMMARY")
        print("=" * 70)

        for table in tables:

            count = self.get_row_count(
                table
            )

            print(
                f"{table:<20} {count}"
            )

        print("=" * 70)
