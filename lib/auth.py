import bcrypt
from app.api.database import db_manager

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def register_user(username, password):
    if not username or not password:
        return None
    hashed_password = hash_password(password)
    return db_manager.insert_user(username, hashed_password)

def login_user(username, password):
    user = db_manager.get_user_by_username(username)
    if user and verify_password(password, user['password_hash']):
        return user
    return None

