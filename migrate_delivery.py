from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    for col, defval in [
        ("delivery_type", "'pickup'"),
        ("delivery_address", "NULL"),
    ]:
        try:
            conn.execute(text(f"ALTER TABLE orders ADD COLUMN {col} VARCHAR DEFAULT {defval}"))
            conn.commit()
            print(f"Column orders.{col} added OK")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"Column orders.{col} already exists, OK")
            else:
                print(f"Error on {col}: {e}")
