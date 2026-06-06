from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE audit_logs ADD COLUMN severity VARCHAR DEFAULT 'info'"))
        conn.commit()
        print("Column severity added OK")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("Column already exists, OK")
        else:
            print(f"Error: {e}")
