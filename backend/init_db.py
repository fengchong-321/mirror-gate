"""Initialize database tables."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine
from app.models import mock, api_test, ui_test, user, scheduler  # Import models to register them with Base


def init_db():
    """Create all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")


if __name__ == "__main__":
    init_db()
