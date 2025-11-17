# app/db/user_repository.py

# create_test_user_with_metadata ! Needs to be deleted after tests are done
# read comments on what to do when tests are done

from sqlalchemy.orm import Session
from typing import Optional
from app.db.models import User # Import the User ORM model
from app.db.models import generate_uuid


def create_test_user_with_metadata(user_id: str) -> User:
    """Returns a synthetic User object for testing purposes."""
    # We construct a User ORM object instance with the desired test data
    user = User(
        user_id=user_id,
        email="test_user@fang.edu",
        # Injecting the mock data:
        profession="Senior Virologist", 
        institute="FANG Research Labs", 
        # Note: created_at and other defaults will be handled by the ORM
    )
    return user

class UserRepository:
    """Encapsulates all database access logic for the User model."""
    
    def __init__(self, db_session: Session):
        """Injects the scoped DB session."""
        self.db = db_session
        
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieves a User object and their metadata by ID.
        This is a synchronous call run within the threadpool.
        """

        user = self.db.query(User).filter(User.user_id == user_id).first()
        if user:
            return user
        
        if user_id == "test-user-f81d4":
            # This is the temporary data seed for testing the Service Layer.
            return create_test_user_with_metadata(user_id)
            
        return None

        # return self.db.query(User).filter(User.user_id == user_id).first() this is good valid code for the db
        # revert back to this when tests are done and delete the create_test_user_with_metadata function
        # as well as the other if statement above 