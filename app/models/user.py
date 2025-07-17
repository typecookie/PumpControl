from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
from functools import wraps
from flask import jsonify

class UserRole(Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMINISTRATOR = "admin"

class User(UserMixin):
    def __init__(self, id, username, role, password_hash):
        self.id = id
        self.username = username
        self.role = role
        self.password_hash = password_hash

    @staticmethod
    def set_password(password):
        return generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        return self.role == role

# Add the decorator function here
def operator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.has_role(UserRole.OPERATOR) and not current_user.has_role(UserRole.ADMINISTRATOR):
            return jsonify({'status': 'error', 'message': 'Operator privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function