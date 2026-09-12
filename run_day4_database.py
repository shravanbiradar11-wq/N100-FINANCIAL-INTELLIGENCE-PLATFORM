from src.etl.database_loader import DatabaseLoader


def main():

    print("\n" + "=" * 70)
    print("SPRINT 1 - DAY 04")
    print("SQLITE DATABASE SCHEMA")
    print("=" * 70)

    # =====================================================
    # CREATE DATABASE LOADER
    # =====================================================

    database_loader = DatabaseLoader(
        database_path="db/nifty100.db",
        schema_path="db/schema.sql"
    )

    # =====================================================
    # CREATE DATABASE
    # =====================================================

    database_loader.create_database()

    # =====================================================
    # VERIFY DATABASE
    # =====================================================

    database_loader.print_summary()

    print("\n✓ DAY 04 DATABASE SETUP COMPLETED")

    print("=" * 70)


if __name__ == "__main__":

    main()