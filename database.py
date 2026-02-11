import sqlite3
from datetime import datetime
import json
import os
from pathlib import Path

DATABASE_PATH = "socialpay.db"

def get_db():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with all required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_verified INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            referrer_id TEXT,
            joined_at TEXT NOT NULL,
            last_login TEXT
        )
    """)
    
    # Admins table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Wallets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            naira REAL DEFAULT 0.0,
            dollar REAL DEFAULT 0.0,
            completed_tasks INTEGER DEFAULT 0,
            pending_tasks INTEGER DEFAULT 0,
            referral_count INTEGER DEFAULT 0,
            referral_naira REAL DEFAULT 0.0,
            referral_dollar REAL DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            platform TEXT NOT NULL,
            task_type TEXT NOT NULL,
            link TEXT NOT NULL,
            currency TEXT NOT NULL,
            price_naira REAL DEFAULT 0.0,
            price_dollar REAL DEFAULT 0.0,
            status TEXT DEFAULT 'active',
            max_users INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            created_by TEXT NOT NULL
        )
    """)
    
    # Task completions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(task_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(task_id, user_id)
        )
    """)
    
    # Submissions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            photo_url TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            submitted_at TEXT NOT NULL,
            processed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (task_id) REFERENCES tasks(task_id)
        )
    """)
    
    # Referrals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id TEXT NOT NULL,
            referred_user_id TEXT NOT NULL,
            tasks_completed INTEGER DEFAULT 0,
            reward_paid INTEGER DEFAULT 0,
            joined_at TEXT NOT NULL,
            FOREIGN KEY (referrer_id) REFERENCES users(user_id),
            FOREIGN KEY (referred_user_id) REFERENCES users(user_id)
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            processed_at TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Withdrawals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            withdrawal_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            currency TEXT NOT NULL,
            amount REAL NOT NULL,
            fee REAL NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            requested_at TEXT NOT NULL,
            approved_at TEXT,
            cancelled_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Exchanges table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exchanges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exchange_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            exchange_type TEXT NOT NULL,
            amount REAL NOT NULL,
            received_amount REAL,
            status TEXT DEFAULT 'pending',
            requested_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Payment details table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            payment_type TEXT NOT NULL,
            details TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Support messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            message TEXT NOT NULL,
            reply TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            replied_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Verification codes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            phone TEXT,
            code TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            verified INTEGER DEFAULT 0
        )
    """)
    
    # PIN management table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            pin_hash TEXT NOT NULL,
            failed_attempts INTEGER DEFAULT 0,
            lockout_until TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Transfer limits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transfer_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, date)
        )
    """)
    
    # Transfer audit log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transfer_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_id TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            from_user TEXT,
            to_user TEXT,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            reason TEXT,
            admin_id TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    
    # Create default admin
    create_default_admin()

def create_default_admin():
    """Create default admin account"""
    from app.auth import hash_password
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM admins WHERE username = ?", ("Ahmerdee",))
    if not cursor.fetchone():
        hashed = hash_password("Ahmerdee4622")
        cursor.execute(
            "INSERT INTO admins (username, password_hash, created_at) VALUES (?, ?, ?)",
            ("Ahmerdee", hashed, datetime.now().isoformat())
        )
        conn.commit()
        print("✅ Default admin created: Ahmerdee")
    
    conn.close()