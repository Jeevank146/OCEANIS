import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, init_db
from sqlalchemy import inspect, text

def sync_schema():
    init_db()
    insp = inspect(engine)
    cols = [c['name'] for c in insp.get_columns('marine_observations')]
    print("Existing marine_observations columns:", cols)

    with engine.connect() as conn:
        for col in ['salinity_psu', 'sea_level_m', 'confidence_score']:
            if col not in cols:
                print(f"Adding missing column {col} to marine_observations...")
                conn.execute(text(f"ALTER TABLE marine_observations ADD COLUMN IF NOT EXISTS {col} DOUBLE PRECISION;"))
                conn.commit()
    
    updated_cols = [c['name'] for c in inspect(engine).get_columns('marine_observations')]
    print("Updated marine_observations columns:", updated_cols)
    print("Schema synchronization complete.")

if __name__ == "__main__":
    sync_schema()
