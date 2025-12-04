"""
One-time migration script to add monitoring columns to Idea table.
Run this ONCE on production after deploying the new schema.

Usage:
    python migrate_db.py
"""

from sqlalchemy import create_engine, text
from config.settings import settings

def migrate():
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='ideas' AND column_name IN ('monitoring_enabled', 'monitoring_ends_at')
        """))
        existing_columns = [row[0] for row in result]

        if 'monitoring_enabled' not in existing_columns:
            print("Adding monitoring_enabled column...")
            conn.execute(text("ALTER TABLE ideas ADD COLUMN monitoring_enabled BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("✓ Added monitoring_enabled")
        else:
            print("✓ monitoring_enabled already exists")

        if 'monitoring_ends_at' not in existing_columns:
            print("Adding monitoring_ends_at column...")
            conn.execute(text("ALTER TABLE ideas ADD COLUMN monitoring_ends_at TIMESTAMP"))
            conn.commit()
            print("✓ Added monitoring_ends_at")
        else:
            print("✓ monitoring_ends_at already exists")

        # Check if ScanHistory table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'scan_history'
            )
        """))
        table_exists = result.scalar()

        if table_exists:
            print("✓ scan_history table already exists")
        else:
            print("Creating scan_history table...")
            # Let init_db() handle this - it will create missing tables
            from database.connection import init_db
            init_db()
            print("✓ Created scan_history table")

    print("\n✅ Migration complete!")

if __name__ == "__main__":
    migrate()
