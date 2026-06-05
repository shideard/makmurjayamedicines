from sqlalchemy.orm import Session
from datetime import datetime
from app.models.models import InventoryBatch
from app.repositories.repositories import medicine_repo, batch_repo

class InventoryService:
    @staticmethod
    def deduct_stock_fifo(db: Session, medicine_id: str, quantity_to_deduct: int):
        """
        Deducts stock using First-In, First-Out (FIFO) logic based on expiry_date.
        Only considers batches that are not expired.
        """
        batches = db.query(InventoryBatch).filter(
            InventoryBatch.medicine_id == medicine_id,
            InventoryBatch.quantity > 0,
            InventoryBatch.expiry_date > datetime.utcnow()
        ).order_by(InventoryBatch.expiry_date.asc()).all()

        remaining_to_deduct = quantity_to_deduct
        updated_batches = []

        for batch in batches:
            if remaining_to_deduct <= 0:
                break

            deducted_from_batch = min(batch.quantity, remaining_to_deduct)
            remaining_to_deduct -= deducted_from_batch

            batch.quantity -= deducted_from_batch
            db.add(batch)
            
            updated_batches.append({
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "deducted": deducted_from_batch
            })

        if remaining_to_deduct > 0:
            raise ValueError(f"Stok tidak mencukupi untuk obat ID: {medicine_id}. Kurang: {remaining_to_deduct}")

        db.commit()
        return updated_batches

    @staticmethod
    def get_total_stock(db: Session, medicine_id: str) -> int:
        batches = db.query(InventoryBatch).filter(
            InventoryBatch.medicine_id == medicine_id,
            InventoryBatch.expiry_date > datetime.utcnow()
        ).all()
        return sum(b.quantity for b in batches)
