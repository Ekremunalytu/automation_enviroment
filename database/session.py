"""
database/session.py
==================

SQLAlchemy Database Connection Configuration
----------------------------------------------

This module configures the SQLAlchemy database connection, including
the engine and session factory. It serves as the foundation for all
database operations in the application.

Architecture Position:
    FastAPI App → Dependency Injection → Session → **Engine** → PostgreSQL

Components:
    1. Engine: Low-level database connection manager
    2. SessionLocal: Factory for creating database sessions
    3. Connection Pool: Manages reusable database connections

Why SQLAlchemy 2.0 Style?
    This configuration uses the "future=True" flag for SQLAlchemy 2.0
    compatibility. This enables:
    - New query syntax (select() instead of query())
    - Better async support preparation
    - Stricter behavior for catching issues early

Connection Pooling:
    SQLAlchemy automatically manages a connection pool. This prevents:
    - Opening too many connections to the database
    - The overhead of establishing new connections
    - Connection exhaustion under load

Usage:
    from database.session import SessionLocal
    from sqlalchemy import select

    # Create a session
    db = SessionLocal()
    try:
        # Use the session with SQLAlchemy 2.0 style
        result = db.scalars(select(MyModel)).all()
    finally:
        db.close()

    # Or use the dependency injection in FastAPI (preferred)
    from core.deps import get_db
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings

# =============================================================================
# Database Engine Configuration
# =============================================================================

engine = create_engine(
    str(settings.db.url),
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)
"""
SQLAlchemy Engine - The core database connection manager.

Parameters:
    DATABASE_URL: Connection string from settings
                  Format: postgresql://user:pass@host:port/dbname

    echo: SQL query logging
          - False: Quiet mode (production)
          - True: Print all SQL queries to stdout (debugging)
          Tip: Set True temporarily to debug query issues

    future: SQLAlchemy 2.0 compatibility mode
            Enables new-style query patterns and behaviors

Connection Pool (Optimized Settings):
    - pool_size: 20 connections (increased from default 5)
    - max_overflow: 40 additional connections beyond pool_size
    - pool_timeout: 30 seconds wait for available connection
    - pool_recycle: 3600 seconds (1 hour) - recycle connections to prevent stale
      connections
    - pool_pre_ping: True - verify connections before use (prevents "connection
      lost" errors)

Performance Benefits:
    - Higher pool_size handles concurrent requests better
    - pool_pre_ping prevents failed queries from stale connections
    - pool_recycle ensures fresh connections periodically
"""


# =============================================================================
# Session Factory Configuration
# =============================================================================

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
"""
Session Factory - Creates database sessions for request handling.

This is a factory function, not a session itself. Call it to get a session:
    session = SessionLocal()

Parameters:
    autocommit: Transaction auto-commit behavior
                - False: Explicit commit() required (recommended)
                - True: Each query auto-commits (not recommended)
                We use False for proper transaction control.

    autoflush: Automatic flushing before queries
               - False: No auto-flush (explicit flush/commit needed)
               - True: Flush pending changes before each query
               We use False for predictable behavior.

    bind: The engine to use for connections

    future: SQLAlchemy 2.0 session behavior

Transaction Behavior:
    With autocommit=False and autoflush=False:
    1. Changes are staged in session (add, delete, modify)
    2. Nothing sent to database until flush() or commit()
    3. commit() flushes pending changes and commits transaction
    4. rollback() discards pending changes
    5. close() returns connection to pool

Example Transaction:
    db = SessionLocal()
    try:
        db.add(new_item)      # Staged, not sent to DB
        db.add(another_item)  # Staged, not sent to DB
        db.commit()           # Both items inserted atomically
    except Exception:
        db.rollback()         # Discard changes on error
    finally:
        db.close()            # Always return to pool

Why Not autoflush=True?
    - Predictable behavior: You control when queries hit the DB
    - Performance: Fewer round-trips to database
    - Transaction integrity: All changes committed together
    - Debugging: Easier to understand query timing

Why Not autocommit=True?
    - Transaction safety: Multiple operations should be atomic
    - Rollback capability: Can undo partial changes on error
    - Consistency: Read-your-writes within transaction
"""
