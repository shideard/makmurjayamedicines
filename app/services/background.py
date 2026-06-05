import csv
import logging
import time
import asyncio
from typing import List
from io import StringIO
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Medicine

logger = logging.getLogger(__name__)

async def simulate_send_email(email_to: str, subject: str, message: str):
    """
    Simulates sending an email via background task.
    """
    logger.warning(f"Preparing to send email to {email_to}...")
    await asyncio.sleep(2) # Simulate network delay
    logger.warning(f"EMAIL SENT TO: {email_to}")
    logger.warning(f"SUBJECT: {subject}")
    logger.warning(f"MESSAGE: {message}")
    logger.warning("=================================")

def process_csv_import_sync(file_content: str, category_id: str):
    """
    Processes a large CSV file in the background.
    Expected CSV columns: name, slug, price, description
    """
    logger.warning("Starting background CSV import...")
    db = SessionLocal()
    try:
        reader = csv.DictReader(StringIO(file_content))
        count = 0
        
        for row in reader:
            # Simulate heavy processing (e.g. image processing, API calls)
            time.sleep(0.1) 
            
            # Use default supplier for demo or ignore
            new_med = Medicine(
                name=row.get('name', 'Unknown'),
                slug=row.get('slug', f"slug-{time.time()}"),
                price=float(row.get('price', 0)),
                description=row.get('description', ''),
                category_id=category_id
            )
            db.add(new_med)
            count += 1
            
            # Commit in chunks to avoid memory bloat
            if count % 50 == 0:
                db.commit()
                
        db.commit()
        logger.warning(f"Successfully imported {count} medicines.")
        
        # Trigger WebSocket notification (we will call the ws manager from the router ideally)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to import CSV: {e}")
    finally:
        db.close()
