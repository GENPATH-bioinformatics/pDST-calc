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
                
                # -- Users table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL
                    )
                """)
                
                # -- Session table
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
                
                # -- Drugs table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS drugs (
                        drug_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        default_dilution TEXT,
                        default_molecular_weight REAL,
                        critical_value REAL,
                        available BOOLEAN
                    )
                """)
                
                # Indexes for better performance (?)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_session_user_id ON session(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_session_date ON session(session_date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_drugs_name ON drugs(name)")
                
                # Check if there are any drugs in the database
                cursor = conn.execute("SELECT COUNT(*) FROM drugs")
                drug_count = cursor.fetchone()[0]
                
                if drug_count == 0:
                    logger.info("Populating drugs table with default drug data...")
                    
                    default_drugs = [
                        ('Amikacin (AMK)', 'WATER', 585.6, 1.0, True),
                        ('Bedaquiline (BDQ)', 'DMSO', 555.5, 1.0, True),
                        ('Clofazimine (CFZ)', 'DMSO', 473.39, 1.0, True),
                        ('Cycloserine (CYC)', 'WATER', 102.09, 1.0, True),
                        ('Delamanid (DMD)', 'DMSO', 534.48, 0.06, True),
                        ('Ethambutol hydrochloride (EMB hyd)', 'WATER', 204.31, 5.0, True),
                        ('Ethionamide (ETH)', 'DMSO', 166.24, 5.0, True),
                        ('Imipenem (IPM)', 'PHOSPHATE PH 7.2', 299.35, 1.0, True),
                        ('Isoniazid CC (INH)-cc', 'WATER', 137.14, 1.0, True),
                        ('Isoniazid high (INH)-h', 'WATER', 137.14, 10.0, True),
                        ('Isoniazid low (INH)-l', 'WATER', 137.14, 0.05, True),
                        ('Levofloxacin (LVX)', '1/2 VOLUME OF WATER THEN 0.1 MOL/L NAOH DROPWISE TO DISSOLVE/WATER', 361.37, 1.0, True),
                        ('Linezolid (LZD)', 'WATER', 337.35, 1.0, True),
                        ('Meropenem (MRP)', 'WATER', 383.46, 1.0, True),
                        ('Moxifloxacin hydrochloride (MFX hyd)', 'WATER', 437.89, 0.25, True),
                        ('Para-aminosalicylic Acid (PAS)', 'WATER OR DMSO', 153.14, 4.0, True),
                        ('Pretomanid (PA-824)', 'DMSO', 359.3, 1.0, True),
                        ('Prothionamide (PTO)', 'DMSO AND WATER', 180.27, 2.5, True),
                        ('Rifabutin (RBT)', 'DMSO', 847.02, 0.5, True),
                        ('Rifampicin (RIF)', 'WATER', 822.94, 2.0, True),
                        ('Streptomycin sulfate salt (STM)', 'WATER', 1457.38, 1.0, True)
                    ]
                    
                    # Insert all default drugs
                    for drug_data in default_drugs:
                        conn.execute("""
                            INSERT INTO drugs (name, default_dilution, default_molecular_weight, critical_value, available)
                            VALUES (?, ?, ?, ?, ?)
                        """, drug_data)
                    
                    logger.info(f"Successfully inserted {len(default_drugs)} default drugs")
                
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

    def get_or_create_session(self, user_id: int, session_name: str) -> Optional[int]:
        """Return existing session_id or create a new session (write operation possible)."""
        try:
            with self.get_connection() as conn:
                cur = conn.execute(
                    "SELECT session_id FROM session WHERE user_id = ? AND session_name = ?",
                    (user_id, session_name)
                )
                row = cur.fetchone()
                if row:
                    return row[0]
                cur = conn.execute(
                    "INSERT INTO session (user_id, session_name, preparation) VALUES (?, ?, ?)",
                    (user_id, session_name, json.dumps({}))
                )
                conn.commit()
                return cur.lastrowid
        except sqlite3.Error:
            return None
        
    def update_session_data(self, session_id: int, preparation: Dict[str, Any]) -> bool:
        """Update session preparation JSON (write operation)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE session SET preparation = ? WHERE session_id = ?",
                    (json.dumps(preparation), session_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
            
    def insert_drug(self, name: str, default_dilution: str = None, 
                   default_molecular_weight: float = None,
                   critical_value: float = None, available: bool = True) -> Optional[int]:
        """Insert a new drug into the database.
        
        Args:
            name: Drug name
            default_dilution: Default dilution value
            default_molecular_weight: Default molecular weight
            critical_value: Critical value
            
        Returns:
            Drug ID if successful, None if failed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO drugs (name, default_dilution, default_molecular_weight, 
                       critical_value, available) VALUES (?, ?, ?, ?, ?)""",
                    (name, default_dilution, default_molecular_weight, critical_value, available)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Drug '{name}' already exists")
            return None
        except sqlite3.Error as e:
            logger.error(f"Error inserting drug: {e}")
            return None


    def delete_drug(self, drug_id: int) -> bool:
        """Delete a drug (write operation)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("DELETE FROM drugs WHERE drug_id = ?", (drug_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def update_drug_availability(self, drug_id: int, available: bool) -> bool:
        """Update the availability status of a drug (write operation)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE drugs SET available = ? WHERE drug_id = ?",
                    (available, drug_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    # Read helpers used by higher layers
    def get_all_drugs(self) -> list:
        """Get all drugs with fields needed by higher layers."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT drug_id, name, default_dilution, default_molecular_weight, critical_value, available FROM drugs"
                )
                drugs = []
                for row in cursor.fetchall():
                    drugs.append({
                        'drug_id': row[0],
                        'name': row[1],
                        'default_dilution': row[2],
                        'default_molecular_weight': row[3],
                        'critical_value': row[4],
                        'available': bool(row[5])
                    })
                return drugs
        except sqlite3.Error as e:
            logger.error(f"Error getting drugs: {e}")
            return []

    def get_sessiones_by_user(self, user_id: int) -> list:
        """Return sessions for a user (name kept for backward compatibility)."""
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

# Global database manager instance
db_manager = DatabaseManager()


