import os
import json
from ..models.user import User, UserRole

class UserManager:
    _users = {}
    _users_file = os.path.join(os.path.expanduser('~'), '.pump_control', 'users.json')

    @classmethod
    def save_users(cls):
        """Save users to file"""
        try:
            # Convert users to serializable format
            users_data = {
                str(user_id): {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role.value,
                    'password_hash': user.password_hash
                }
                for user_id, user in cls._users.items()
            }

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(cls._users_file), exist_ok=True)

            # Save to file
            with open(cls._users_file, 'w') as f:
                json.dump(users_data, f, indent=4)
            print("Users saved successfully")
        except Exception as e:
            print(f"Error saving users: {str(e)}")

    @classmethod
    def load_users(cls):
        """Load users from file"""
        try:
            if os.path.exists(cls._users_file):
                with open(cls._users_file, 'r') as f:
                    users_data = json.load(f)
                
                cls._users = {
                    int(user_id): User(
                        id=data['id'],
                        username=data['username'],
                        role=UserRole(data['role']),
                        password_hash=data['password_hash']
                    )
                    for user_id, data in users_data.items()
                }
                print("Users loaded successfully")
            else:
                print("No users file found, will create with defaults")
                cls._users = {}
        except Exception as e:
            print(f"Error loading users: {str(e)}")
            cls._users = {}

    @classmethod
    def init_default_users(cls):
        """Initialize default users if none exist"""
        cls.load_users()  # First load any existing users
        
        if not cls._users:
            print("Creating default users")
            # Create default admin user
            cls.create_user("admin", "admin", UserRole.ADMINISTRATOR)
            # Create default operator user
            cls.create_user("operator", "operator", UserRole.OPERATOR)
            # Create default viewer user
            cls.create_user("viewer", "viewer", UserRole.VIEWER)
            
            # Save the default users
            cls.save_users()

    @classmethod
    def create_user(cls, username, password, role):
        """Create a new user and save to file"""
        if cls.get_user_by_username(username):
            raise ValueError("Username already exists")

        user_id = max(cls._users.keys()) + 1 if cls._users else 1
        user = User(
            id=user_id,
            username=username,
            role=role,
            password_hash=User.set_password(password)
        )
        cls._users[user_id] = user
        cls.save_users()  # Save after creating new user
        return user

    @classmethod
    def get_user_by_id(cls, user_id):
        return cls._users.get(user_id)

    @classmethod
    def get_user_by_username(cls, username):
        for user in cls._users.values():
            if user.username == username:
                return user
        return None

    @classmethod
    def delete_user(cls, user_id):
        """Delete a user and save changes"""
        if user_id in cls._users:
            del cls._users[user_id]
            cls.save_users()
            return True
        return False

@classmethod
def reset_password(cls, user_id, new_password):
    """Reset a user's password"""
    if user_id in cls._users:
        user = cls._users[user_id]
        user.password_hash = User.set_password(new_password)
        cls.save_users()
        return True
    return False

@classmethod
def get_all_users(cls):
    """Get all users"""
    return list(cls._users.values())

@classmethod
def update_user_role(cls, user_id, new_role):
    """Update a user's role"""
    if user_id in cls._users:
        user = cls._users[user_id]
        user.role = new_role
        cls.save_users()
        return True
    return False