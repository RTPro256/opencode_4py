"""
Database connection management for OpenCode.

Provides async database operations using SQLAlchemy 2.0 and aiosqlite.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from opencode.db.models import Base


class Database:
    """
    Async database manager for OpenCode.
    
    Manages the SQLite database connection and provides
    session management for async operations.
    """
    
    def __init__(
        self,
        db_path: Path,
        echo: bool = False,
    ) -> None:
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
            echo: Whether to echo SQL statements (for debugging)
        """
        self.db_path = db_path
        self.echo = echo
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
    
    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine, creating it if necessary."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory, creating it if necessary."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._session_factory
    
    async def init(self) -> None:
        """Initialize the database connection and create tables."""
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create async engine
        db_url = f"sqlite+aiosqlite:///{self.db_path}"
        
        self._engine = create_async_engine(
            db_url,
            echo=self.echo,
            poolclass=StaticPool,  # Better for SQLite
            connect_args={
                "check_same_thread": False,
            },
        )
        
        # Enable foreign keys for SQLite
        @event.listens_for(self._engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
        
        # Create session factory
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        
        # Create tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self) -> None:
        """Close the database connection."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session as an async context manager.
        
        Usage:
            async with db.session() as session:
                result = await session.execute(...)
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def get_session(self) -> AsyncSession:
        """Get a new database session (caller is responsible for closing)."""
        return self.session_factory()
    
    async def execute_raw(self, sql: str, params: Optional[dict] = None) -> None:
        """Execute raw SQL."""
        async with self.engine.begin() as conn:
            await conn.execute(sql, params or {})
    
    async def vacuum(self) -> None:
        """Run VACUUM to optimize the database."""
        await self.execute_raw("VACUUM")


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get the global database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db


async def init_database(db_path: Path, echo: bool = False) -> Database:
    """
    Initialize the global database instance.
    
    Args:
        db_path: Path to the SQLite database file
        echo: Whether to echo SQL statements
        
    Returns:
        The initialized Database instance
    """
    global _db
    _db = Database(db_path=db_path, echo=echo)
    await _db.init()
    return _db


async def close_database() -> None:
    """Close the global database instance."""
    global _db
    if _db:
        await _db.close()
        _db = None
