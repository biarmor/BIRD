from app.database import DatabaseManager
from app.models import User
from app.security import hash_password
import uuid

print("Initializing database...")
DatabaseManager.initialize()
db = DatabaseManager.get_session()
try:
    print("Creating user...")
    user = User(
        id=str(uuid.uuid4()),
        username="testuser_db",
        email="testuser_db@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User"
    )
    db.add(user)
    db.commit()
    print("✅ User created successfully in DB!")
except Exception as e:
    print(f"❌ DB Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
