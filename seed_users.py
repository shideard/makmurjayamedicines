import os
import sys

# Append the current directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import Base, Role, User
from app.core.security import get_password_hash

def seed_data():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Define roles
        role_names = ["Admin", "Apoteker", "Kasir", "Pelanggan"]
        roles = {}
        for r_name in role_names:
            role = db.query(Role).filter(Role.name == r_name).first()
            if not role:
                role = Role(name=r_name)
                db.add(role)
                db.commit()
                db.refresh(role)
            roles[r_name] = role
            
        print("Roles seeded.")

        # Define users
        users_data = [
            {"name": "Budi (Admin)", "email": "admin@makmurjaya.com", "password": "Password123!", "role": roles["Admin"].id},
            {"name": "Siti (Apoteker)", "email": "apoteker@makmurjaya.com", "password": "Password123!", "role": roles["Apoteker"].id},
            {"name": "Agus (Kasir)", "email": "kasir@makmurjaya.com", "password": "Password123!", "role": roles["Kasir"].id},
            {"name": "Rina (Pelanggan)", "email": "pasien@gmail.com", "password": "Password123!", "role": roles["Pelanggan"].id},
        ]

        for u in users_data:
            user = db.query(User).filter(User.email == u["email"]).first()
            if not user:
                hashed_pw = get_password_hash(u["password"])
                new_user = User(
                    name=u["name"],
                    email=u["email"],
                    hashed_password=hashed_pw,
                    role_id=u["role"]
                )
                db.add(new_user)
        
        db.commit()
        print("Users seeded successfully!")
        print("\n--- Akun Default Ujian BNSP ---")
        for u in users_data:
            print(f"Role: {u['name'].split('(')[1].replace(')','')}")
            print(f"Email: {u['email']}")
            print(f"Password: {u['password']}")
            print("-" * 30)

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
