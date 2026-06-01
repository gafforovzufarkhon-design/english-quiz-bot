"""
Database module for storing user data persistently.
Supports SQLite (for local development) and PostgreSQL (for production).
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any

# Try to import psycopg2 for PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import Json
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logging.warning("psycopg2 not available. Using SQLite for data storage.")

# Try to import sqlite3 (always available in Python)
import sqlite3

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")  # For production (Render, Heroku, etc.)
USE_SQLITE = not DATABASE_URL or not PSYCOPG2_AVAILABLE

# SQLite database file
SQLITE_DB_FILE = "users_data.db"


class Database:
    """Database handler for user data storage."""
    
    def __init__(self):
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database connection."""
        if USE_SQLITE:
            self._init_sqlite()
        else:
            self._init_postgresql()
    
    def _init_sqlite(self):
        """Initialize SQLite database."""
        logger.info("Initializing SQLite database...")
        self.conn = sqlite3.connect(SQLITE_DB_FILE, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Create table if not exists
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        self.conn.commit()
        logger.info("SQLite database initialized successfully.")
    
    def _init_postgresql(self):
        """Initialize PostgreSQL database."""
        if not PSYCOPG2_AVAILABLE:
            logger.error("psycopg2 not available, falling back to SQLite")
            self._init_sqlite()
            return
        
        logger.info("Initializing PostgreSQL database...")
        try:
            self.conn = psycopg2.connect(DATABASE_URL)
            self.conn.autocommit = False
            
            # Create table if not exists
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        data JSONB NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """)
            self.conn.commit()
            logger.info("PostgreSQL database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}. Falling back to SQLite.")
            self._init_sqlite()
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from database."""
        try:
            if USE_SQLITE or not PSYCOPG2_AVAILABLE:
                return self._get_user_sqlite(user_id)
            else:
                return self._get_user_postgresql(user_id)
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def _get_user_sqlite(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from SQLite."""
        cursor = self.conn.execute(
            "SELECT data FROM users WHERE user_id = ?", 
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row["data"])
        return None
    
    def _get_user_postgresql(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from PostgreSQL."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT data FROM users WHERE user_id = %s", 
                    (user_id,)
                )
                row = cur.fetchone()
                if row:
                    return row[0]
        except Exception as e:
            logger.error(f"PostgreSQL error: {e}")
        return None
    
    def save_user(self, user_id: str, data: Dict[str, Any]):
        """Save user data to database."""
        try:
            if USE_SQLITE or not PSYCOPG2_AVAILABLE:
                self._save_user_sqlite(user_id, data)
            else:
                self._save_user_postgresql(user_id, data)
        except Exception as e:
            logger.error(f"Error saving user {user_id}: {e}")
    
    def _save_user_sqlite(self, user_id: str, data: Dict[str, Any]):
        """Save user data to SQLite."""
        self.conn.execute(
            """INSERT OR REPLACE INTO users (user_id, data, updated_at) 
               VALUES (?, ?, ?)""",
            (user_id, json.dumps(data, ensure_ascii=False), time.time())
        )
        self.conn.commit()
    
    def _save_user_postgresql(self, user_id: str, data: Dict[str, Any]):
        """Save user data to PostgreSQL."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO users (user_id, data, updated_at) 
                       VALUES (%s, %s, %s)
                       ON CONFLICT (user_id) 
                       DO UPDATE SET data = EXCLUDED.data, updated_at = EXCLUDED.updated_at""",
                    (user_id, data, time.time())
                )
            self.conn.commit()
        except Exception as e:
            logger.error(f"PostgreSQL error: {e}")
            # Fallback to SQLite
            self._save_user_sqlite(user_id, data)
    
    def get_all_users(self) -> list:
        """Get all users from database."""
        users = []
        try:
            if USE_SQLITE or not PSYCOPG2_AVAILABLE:
                cursor = self.conn.execute("SELECT user_id, data FROM users")
                for row in cursor.fetchall():
                    users.append({
                        "user_id": row["user_id"],
                        "data": json.loads(row["data"])
                    })
            else:
                with self.conn.cursor() as cur:
                    cur.execute("SELECT user_id, data FROM users")
                    for row in cur.fetchall():
                        users.append({
                            "user_id": row[0],
                            "data": row[1]
                        })
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
        return users
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")


# Global database instance
db = Database()


def get_user_data() -> Dict[str, Dict[str, Any]]:
    """Get all user data as a dictionary (for backward compatibility)."""
    users = db.get_all_users()
    return {user["user_id"]: user["data"] for user in users}


def load_user_data() -> Dict[str, Dict[str, Any]]:
    """Load user data (backward compatibility with original function)."""
    return get_user_data()


def save_user_data(data: Dict[str, Dict[str, Any]]):
    """Save all user data (backward compatibility with original function)."""
    for user_id, user_data in data.items():
        db.save_user(user_id, user_data)


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID (backward compatibility)."""
    return db.get_user(user_id)


def save_user_by_id(user_id: str, data: Dict[str, Any]):
    """Save user by ID (backward compatibility)."""
    db.save_user(user_id, data)