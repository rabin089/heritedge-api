import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/heritedge_db")
engine = create_engine(DATABASE_URL)

def make_admin(email: str):
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET role='admin', is_admin=true WHERE email=:email"), {"email": email})

if __name__ == "__main__":
    make_admin("admin@test.com")
    print("OK")
