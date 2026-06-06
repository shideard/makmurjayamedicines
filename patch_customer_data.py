"""
Script to patch existing customer 'Rina' with realistic profile data
seolah-olah sudah terdaftar dari data rekam medis klinik.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import User, Customer

def patch_customer_data():
    db: Session = SessionLocal()
    try:
        # Find the Pelanggan user (Rina)
        user = db.query(User).filter(User.email == "pasien@gmail.com").first()
        if not user:
            print("User pasien@gmail.com not found!")
            return

        # Ensure Customer profile exists
        if not user.customer:
            customer = Customer(user_id=user.id)
            db.add(customer)
            db.commit()
            db.refresh(user)
            customer = user.customer
        else:
            customer = user.customer

        # Fill realistic data (as if registered from medical records)
        customer.phone = "081234567890"
        customer.address = "Jl. Melati No. 12, RT 03/RW 05, Kel. Menteng, Kec. Menteng, Jakarta Pusat, 10310"

        db.commit()
        print(f"Customer profile updated for user: {user.name}")
        print(f"  Phone   : {customer.phone}")
        print(f"  Address : {customer.address}")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    patch_customer_data()
