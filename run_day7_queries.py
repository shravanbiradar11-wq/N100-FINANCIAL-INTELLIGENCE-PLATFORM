import sqlite3
from pathlib import Path


DB_PATH = Path("db/nifty100.db")
SQL_PATH = Path(
    "notebooks/exploratory_queries.sql"
)


def main():

    print("=" * 70)
    print("SPRINT 1 - DAY 07")
    print("EXPLORATORY QUERIES")
    print("=" * 70)

    if not DB_PATH.exists():

        print(
            f"Database not found: {DB_PATH}"
        )

        return

    if not SQL_PATH.exists():

        print(
            f"SQL file not found: {SQL_PATH}"
        )

        return

    connection = sqlite3.connect(
        DB_PATH
    )

    try:

        sql = SQL_PATH.read_text(
            encoding="utf-8"
        )

        queries = [
            query.strip()
            for query in sql.split(";")
            if query.strip()
        ]

        print(
            f"\nQueries found: "
            f"{len(queries)}"
        )

        for index, query in enumerate(
            queries,
            start=1
        ):

            print("\n")
            print("=" * 70)
            print(
                f"QUERY {index}"
            )
            print("=" * 70)

            cursor = connection.execute(
                query
            )

            rows = cursor.fetchall()

            columns = [
                description[0]
                for description
                in cursor.description
            ]

            print(
                " | ".join(columns)
            )

            print("-" * 70)

            for row in rows[:20]:

                print(
                    " | ".join(
                        str(value)
                        for value in row
                    )
                )

            if len(rows) > 20:

                print(
                    f"\nShowing first 20 "
                    f"of {len(rows)} rows."
                )

        print("\n")
        print("=" * 70)
        print("ALL EXPLORATORY QUERIES EXECUTED")
        print("=" * 70)

    finally:

        connection.close()


if __name__ == "__main__":
    main()