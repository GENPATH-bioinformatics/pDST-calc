import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for the DST Calculator."""
    
    def __init__(self, db_path: str = "dstcalc.db"):
        """Initialize database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Create users table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL
                    )
                """)
                
                # Create session table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS session (
                        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        session_name TEXT NOT NULL,
                        session_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        preparation TEXT,  -- JSON string
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Create drugs table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS drugs (
                        drug_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        default_dilution TEXT,
                        default_molecular_weight REAL,
                        mol_max REAL,
                        critical_value REAL
                        available BOOLEAN
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_session_user_id ON session(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_session_date ON session(session_date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_drugs_name ON drugs(name)")
                
                conn.commit()
                logger.info(f"Database initialized successfully at {self.db_path}")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper configuration.
        
        Returns:
            SQLite connection with foreign keys enabled
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def insert_user(self, username: str, password_hash: str) -> Optional[int]:
        """Insert a new user into the database.
        
        Args:
            username: Username for the new user
            password_hash: Hashed password
            
        Returns:
            User ID if successful, None if failed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"User '{username}' already exists")
            return None
        except sqlite3.Error as e:
            logger.error(f"Error inserting user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User dictionary if found, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT user_id, username, password_hash FROM users WHERE username = ?",
                    (username,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'user_id': row[0],
                        'username': row[1],
                        'password_hash': row[2]
                    }
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def insert_session(self, user_id: int, preparation: Dict[str, Any]) -> Optional[int]:
        """Insert a new session record.
        
        Args:
            user_id: ID of the user creating the session
            preparation: Preparation data as dictionary (will be stored as JSON)
            
        Returns:
            session ID if successful, None if failed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO session (user_id, preparation) VALUES (?, ?)",
                    (user_id, json.dumps(preparation))
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error inserting session: {e}")
            return None
    
    def get_sessiones_by_user(self, user_id: int) -> list:
        """Get all sessiones for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of session dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT session_id, session_date, preparation FROM session WHERE user_id = ? ORDER BY session_date DESC",
                    (user_id,)
                )
                sessiones = []
                for row in cursor.fetchall():
                    sessiones.append({
                        'session_id': row[0],
                        'session_date': row[1],
                        'preparation': json.loads(row[2]) if row[2] else {}
                    })
                return sessiones
        except sqlite3.Error as e:
            logger.error(f"Error getting sessiones: {e}")
            return []
    
    def insert_drug(self, name: str, default_dilution: str = None, 
                   default_molecular_weight: float = None, mol_max: float = None, 
                   critical_value: float = None, available: bool = True) -> Optional[int]:
        """Insert a new drug into the database.
        
        Args:
            name: Drug name
            default_dilution: Default dilution value
            default_molecular_weight: Default molecular weight
            mol_max: Maximum molecular value
            critical_value: Critical value
            
        Returns:
            Drug ID if successful, None if failed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO drugs (name, default_dilution, default_molecular_weight, 
                       mol_max, critical_value, available) VALUES (?, ?, ?, ?, ?, ?)""",
                    (name, default_dilution, default_molecular_weight, mol_max, critical_value, available)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Drug '{name}' already exists")
            return None
        except sqlite3.Error as e:
            logger.error(f"Error inserting drug: {e}")
            return None
    
    def get_all_drugs(self) -> list:
        """Get all drugs from the database.
        
        Returns:
            List of drug dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT drug_id, name, default_dilution, default_molecular_weight, mol_max, critical_value, available FROM drugs"
                )
                drugs = []
                for row in cursor.fetchall():
                    drugs.append({
                        'drug_id': row[0],
                        'name': row[1],
                        'default_dilution': row[2],
                        'default_molecular_weight': row[3],
                        'mol_max': row[4],
                        'critical_value': row[5],
                        'available': row[6]
                    })
                return drugs
        except sqlite3.Error as e:
            logger.error(f"Error getting drugs: {e}")
            return []
    
    def get_drug_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get drug information by name.
        
        Args:
            name: Drug name to search for
            
        Returns:
            Drug dictionary if found, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT drug_id, name, default_dilution, default_molecular_weight, mol_max, critical_value, available FROM drugs WHERE name = ?",
                    (name,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        'drug_id': row[0],
                        'name': row[1],
                        'default_dilution': row[2],
                        'default_molecular_weight': row[3],
                        'mol_max': row[4],
                        'critical_value': row[5],
                        'available': row[6]
                    }
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting drug: {e}")
            return None


# Global database manager instance
db_manager = DatabaseManager() 