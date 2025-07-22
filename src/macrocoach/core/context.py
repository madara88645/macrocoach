"""
Application context for sharing state across agents.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import sqlite3
from pathlib import Path


@dataclass
class ApplicationContext:
    """
    Shared context object for all agents.
    No globals - all agents receive this context.
    """
    
    # Database configuration
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./macrocoach.db"))
    
    # API keys
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    
    # Feature flags
    healthkit_enabled: bool = field(default_factory=lambda: os.getenv("APPLE_HEALTHKIT_ENABLED", "false").lower() == "true")
    health_connect_enabled: bool = field(default_factory=lambda: os.getenv("ANDROID_HEALTH_CONNECT_ENABLED", "false").lower() == "true")
    miband_enabled: bool = field(default_factory=lambda: os.getenv("XIAOMI_MIBAND_ENABLED", "false").lower() == "true")
    
    # Application settings
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "true").lower() == "true")
    
    # Runtime state (not persisted)
    _db_connection: Optional[sqlite3.Connection] = field(default=None, init=False)
    _user_sessions: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)
    
    def __post_init__(self):
        """Initialize context after creation."""
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """Ensure the database file exists and create if necessary."""
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            if not db_path.startswith("/"):  # Relative path
                db_path = Path(db_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_db_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._db_connection is None:
            db_path = self.database_url.replace("sqlite:///", "")
            self._db_connection = sqlite3.connect(db_path)
            self._db_connection.row_factory = sqlite3.Row
        return self._db_connection
    
    def close_db_connection(self) -> None:
        """Close database connection."""
        if self._db_connection:
            self._db_connection.close()
            self._db_connection = None
    
    def get_user_session(self, user_id: str) -> Dict[str, Any]:
        """Get or create user session data."""
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = {
                "created_at": None,
                "last_active": None,
                "preferences": {},
                "current_plan": None
            }
        return self._user_sessions[user_id]
    
    def update_user_session(self, user_id: str, data: Dict[str, Any]) -> None:
        """Update user session data."""
        session = self.get_user_session(user_id)
        session.update(data)
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present."""
        if not self.openai_api_key:
            print("Warning: OPENAI_API_KEY not set - meal generation will be limited")
            return False
        return True
