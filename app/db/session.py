from app.database import DatabaseManager

class SessionLocalContext:
    def __enter__(self):
        self.db = DatabaseManager.get_session()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

def SessionLocal():
    """Returns a context manager for database sessions."""
    return SessionLocalContext()
