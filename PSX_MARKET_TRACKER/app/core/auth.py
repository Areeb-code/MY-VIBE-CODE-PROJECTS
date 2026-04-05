"""
PSX Platform — Authentication & Session Management
Handles password hashing, user authentication, registration, and sessions.
"""

import bcrypt
from dataclasses import dataclass
from typing import Optional
from .db import get_connection


# ─── Role Constants ────────────────────────────────────────────────────────────
ROLE_OWNER = "owner"
ROLE_BROKER = "broker"
ROLE_CLIENT = "client"


# ─── Session ───────────────────────────────────────────────────────────────────
@dataclass
class Session:
    """In-memory session object passed throughout the application."""
    user_id: int
    user_name: str
    email: str
    role: str           # 'owner', 'broker', 'client'
    broker_id: Optional[int]  # owner=None, broker=self.id, client=broker's id


# ─── Password Hashing ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


# ─── Authentication ────────────────────────────────────────────────────────────

def authenticate(identifier: str, password: str) -> Optional[Session]:
    """
    Authenticate a user by email/username and password.
    Returns a Session object on success, None on failure.
    """
    conn = get_connection()
    
    # Try matching by email first, then by name
    user = conn.execute(
        "SELECT * FROM users WHERE (email = ? OR name = ?) AND is_active = 1",
        (identifier, identifier)
    ).fetchone()
    
    conn.close()
    
    if not user:
        return None
    
    if not verify_password(password, user['password_hash']):
        return None
    
    return Session(
        user_id=user['id'],
        user_name=user['name'],
        email=user['email'],
        role=user['role'],
        broker_id=user['broker_id']
    )


# ─── User Creation ─────────────────────────────────────────────────────────────

def create_owner(name: str, email: str, password: str) -> Optional[Session]:
    """
    Create the system owner account. Should only be called once (first-run).
    Returns Session on success, None if owner already exists.
    """
    conn = get_connection()
    
    # Check if owner already exists
    existing = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = ?", (ROLE_OWNER,)).fetchone()
    if existing['cnt'] > 0:
        conn.close()
        return None
    
    pw_hash = hash_password(password)
    
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash, role, broker_id) VALUES (?, ?, ?, ?, ?)",
        (name, email, pw_hash, ROLE_OWNER, None)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return Session(
        user_id=user_id,
        user_name=name,
        email=email,
        role=ROLE_OWNER,
        broker_id=None
    )


def register_broker(name: str, email: str, password: str) -> dict:
    """
    Register a new broker account (self-registration from login screen).
    Returns {'success': True, 'session': Session} or {'success': False, 'error': str}
    """
    conn = get_connection()
    
    # Check email uniqueness
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return {'success': False, 'error': 'An account with this email already exists.'}
    
    # Check name uniqueness
    existing_name = conn.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
    if existing_name:
        conn.close()
        return {'success': False, 'error': 'This username is already taken.'}
    
    pw_hash = hash_password(password)
    
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash, role, broker_id) VALUES (?, ?, ?, ?, ?)",
        (name, email, pw_hash, ROLE_BROKER, None)  # broker_id set after insert
    )
    broker_id = cursor.lastrowid
    
    # Set broker_id = own id
    conn.execute("UPDATE users SET broker_id = ? WHERE id = ?", (broker_id, broker_id))
    conn.commit()
    conn.close()
    
    session = Session(
        user_id=broker_id,
        user_name=name,
        email=email,
        role=ROLE_BROKER,
        broker_id=broker_id
    )
    
    return {'success': True, 'session': session}


def create_client(broker_session: Session, name: str, email: str, password: str) -> dict:
    """
    Create a client account under the calling broker.
    Returns {'success': True, 'user_id': int} or {'success': False, 'error': str}
    """
    if broker_session.role not in (ROLE_BROKER, ROLE_OWNER):
        return {'success': False, 'error': 'Only brokers can create client accounts.'}
    
    conn = get_connection()
    
    # Check email uniqueness
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return {'success': False, 'error': 'An account with this email already exists.'}
    
    # Check name uniqueness
    existing_name = conn.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
    if existing_name:
        conn.close()
        return {'success': False, 'error': 'This username is already taken.'}
    
    pw_hash = hash_password(password)
    
    # Client inherits the broker's ID
    the_broker_id = broker_session.user_id if broker_session.role == ROLE_BROKER else broker_session.broker_id
    
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash, role, broker_id) VALUES (?, ?, ?, ?, ?)",
        (name, email, pw_hash, ROLE_CLIENT, the_broker_id)
    )
    client_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {'success': True, 'user_id': client_id}


# ─── User Management ──────────────────────────────────────────────────────────

def change_password(user_id: int, old_password: str, new_password: str) -> tuple:
    """
    Change a user's password.
    Returns (True, "Success") or (False, "Error message")
    """
    conn = get_connection()
    user = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return False, 'User not found.'
    
    if not verify_password(old_password, user['password_hash']):
        conn.close()
        return False, 'Current password is incorrect.'
    
    new_hash = hash_password(new_password)
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()
    
    return True, 'Password updated successfully.'


def get_clients_for_broker(broker_id: int) -> list:
    """Get all clients belonging to a broker."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name, email, is_active, created_at FROM users WHERE role = ? AND broker_id = ? ORDER BY name",
        (ROLE_CLIENT, broker_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_brokers() -> list:
    """Get all broker accounts (for owner use)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name, email, is_active, created_at FROM users WHERE role = ? ORDER BY name",
        (ROLE_BROKER,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_clients() -> list:
    """Get all client accounts (for owner use)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name, email, is_active, created_at FROM users WHERE role = ? ORDER BY name",
        (ROLE_CLIENT,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_users() -> list:
    """Get all non-owner users (for owner use)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name, email, role, broker_id, is_active, created_at FROM users WHERE role != ? ORDER BY role, name",
        (ROLE_OWNER,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_user_active(user_id: int, is_active: bool):
    """Activate or deactivate a user account."""
    conn = get_connection()
    conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id))
    conn.commit()
    conn.close()


def update_user(user_id: int, name: Optional[str] = None, email: Optional[str] = None) -> dict:
    """Update user profile fields."""
    conn = get_connection()
    
    if email:
        existing = conn.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id)).fetchone()
        if existing:
            conn.close()
            return {'success': False, 'error': 'Email already in use.'}
    
    if name:
        existing = conn.execute("SELECT id FROM users WHERE name = ? AND id != ?", (name, user_id)).fetchone()
        if existing:
            conn.close()
            return {'success': False, 'error': 'Username already taken.'}
    
    if name and email:
        conn.execute("UPDATE users SET name = ?, email = ? WHERE id = ?", (name, email, user_id))
    elif name:
        conn.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    elif email:
        conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
    
    conn.commit()
    conn.close()
    return {'success': True}


def get_system_stats() -> dict:
    """Get platform-wide statistics (for owner dashboard)."""
    conn = get_connection()
    
    broker_count = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = ?", (ROLE_BROKER,)).fetchone()['cnt']
    client_count = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = ?", (ROLE_CLIENT,)).fetchone()['cnt']
    total_transactions = conn.execute("SELECT COUNT(*) as cnt FROM portfolio").fetchone()['cnt']
    active_users = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE is_active = 1 AND role != ?", (ROLE_OWNER,)).fetchone()['cnt']
    
    conn.close()
    
    return {
        'broker_count': broker_count,
        'client_count': client_count,
        'total_transactions': total_transactions,
        'active_users': active_users
    }
