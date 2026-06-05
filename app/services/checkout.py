import time
import random
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Order, OrderItem, Payment, Customer
from app.repositories.repositories import medicine_repo, customer_repo
from app.services.inventory import InventoryService

class CheckoutService:
    @staticmethod
    def process_checkout(db: Session, user_id: str, items: List[Dict[str, Any]], payment_method: str):
        """
        Processes a checkout request.
        `items` should be a list of dicts: [{"id": "medicine_id", "quantity": 2, "name": "..."}]
        """
        if not items:
            raise ValueError("Keranjang belanja kosong.")

        # Ensure customer exists for this user
        customer = customer_repo.get_by_user_id(db, user_id)
        if not customer:
            customer = Customer(user_id=user_id)
            db.add(customer)
            db.flush()

        subtotal = 0.0
        order_items_data = []

        try:
            # Validate stock, calculate prices, and deduct via FIFO
            for item in items:
                medicine = medicine_repo.get(db, item["id"])
                if not medicine:
                    raise ValueError(f"Obat tidak ditemukan: {item.get('name', item['id'])}")
                
                quantity = item["quantity"]
                available_stock = InventoryService.get_total_stock(db, medicine.id)
                
                if available_stock < quantity:
                    raise ValueError(f"Stok tidak mencukupi untuk obat: {medicine.name}")

                item_total = medicine.price * quantity
                subtotal += item_total

                order_items_data.append(OrderItem(
                    medicine_id=medicine.id,
                    quantity=quantity,
                    price=medicine.price
                ))

                # Deduct stock
                InventoryService.deduct_stock_fifo(db, medicine.id, quantity)

            tax = subtotal * 0.11
            grand_total = subtotal + tax
            invoice_number = f"INV-{int(time.time())}-{random.randint(100, 999)}"

            # Create Order
            new_order = Order(
                invoice_number=invoice_number,
                customer_id=customer.id,
                status="PENDING",
                total=subtotal,
                tax=tax,
                grand_total=grand_total
            )
            db.add(new_order)
            db.flush() # To get new_order.id

            # Add OrderItems
            for oi in order_items_data:
                oi.order_id = new_order.id
                db.add(oi)

            # Create Payment
            new_payment = Payment(
                order_id=new_order.id,
                amount=grand_total,
                method=payment_method,
                status="PENDING"
            )
            db.add(new_payment)

            db.commit()
            db.refresh(new_order)
            return new_order

        except Exception as e:
            db.rollback()
            raise e
