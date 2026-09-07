import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from database import engine, init_db
import models  # Ensures all model classes are registered with Base.metadata


def init_database() -> list[str]:
    """
    Safely creates all database tables defined in SQLAlchemy metadata.
    Returns the list of table names present in the database.
    """
    init_db()
    inspector = inspect(engine)
    return inspector.get_table_names()


def verify_tables() -> dict:
    """
    Inspects and returns metadata about created tables, columns, and indexes.
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    table_details = {}

    target_tables = [
        "data_sources",
        "data_refresh_logs",
        "weather_observations",
        "marine_observations",
        "earth_observations",
        "ports",
        "restricted_zones",
        "protected_zones",
        "marine_alerts",
        "cyclone_tracks",
        "hazard_zones",
        "marine_operations",
    ]

    for table in target_tables:
        if table in tables:
            columns = [c["name"] for c in inspector.get_columns(table)]
            indexes = [i["name"] for i in inspector.get_indexes(table)]
            table_details[table] = {
                "exists": True,
                "columns": columns,
                "indexes": indexes,
            }
        else:
            table_details[table] = {"exists": False}

    return table_details


if __name__ == "__main__":
    print("Initializing OCEANIS database tables...")
    existing_tables = init_database()
    print(f"All tables in database: {existing_tables}")
    details = verify_tables()
    print("\nVerified Tables Structure:")
    for table_name, meta in details.items():
        print(f"  - {table_name}: exists={meta.get('exists')}, columns={meta.get('columns', [])}")
