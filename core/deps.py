"""
core/deps.py
============

FastAPI Dependency Injection Providers
--------------------------------------

This module contains dependency injection functions used throughout
the FastAPI application. Dependencies are functions that provide
shared resources to route handlers.

What is Dependency Injection (DI)?
    DI is a design pattern where objects receive their dependencies
    from an external source rather than creating them internally.
    FastAPI's Depends() function implements this pattern.

Why Use DI?
    1. Testability: Easy to mock dependencies in tests
    2. Reusability: Same dependency used across multiple endpoints
    3. Lifecycle Management: Proper resource cleanup (sessions, connections)
    4. Decoupling: Routes don't need to know how to create dependencies

Common Dependencies in This Project:
    - get_db: Provides database sessions with automatic cleanup
    - (Future) get_current_user: Authentication/authorization
    - (Future) get_redis: Cache connection management

Usage in Routes:
    from core.deps import get_db
    from fastapi import Depends

    @router.get("/items")
    def get_items(db: Session = Depends(get_db)):
        # db session is automatically created and cleaned up
        return db.execute(select(Item)).scalars().all()

Database Session Lifecycle:
    1. Request arrives at endpoint
    2. FastAPI calls get_db() to create session
    3. Session is yielded to route handler
    4. Route handler uses session for DB operations
    5. After response (success or error), finally block closes session
    6. Session is returned to connection pool
"""

from collections.abc import Generator

from database.session import SessionLocal


def get_db() -> Generator:
    """
    Create and yield a database session for request handling.

    This is a generator-based dependency that implements the
    "context manager" pattern for database session management.

    The session lifecycle:
        1. Session is created from SessionLocal factory
        2. Session is yielded to the route handler
        3. After request completes, finally block ensures cleanup
        4. Session is closed, returning connection to pool

    Yields:
        Session: SQLAlchemy session bound to PostgreSQL

    Usage:
        @router.get("/example")
        def example_route(db: Session = Depends(get_db)):
            # db is available and will be automatically closed
            items = db.execute(select(MyModel)).scalars().all()
            return items

    Why Generator Pattern?
        - Ensures cleanup even if route handler raises exception
        - FastAPI recognizes yield-based deps for lifecycle management
        - Connection is always returned to pool (no leaks)

    Transaction Behavior:
        - autocommit=False: Changes require explicit commit()
        - autoflush=False: Changes not flushed until commit
        - Each request gets an isolated transaction

    Error Handling:
        - Exceptions in route handler: Session still closed
        - Connection errors: SQLAlchemy handles reconnection
        - Rollback should be done in route/service layer

    Example with Transaction:
        @router.post("/create")
        def create_item(item: ItemCreate, db: Session = Depends(get_db)):
            try:
                new_item = Item(**item.model_dump())
                db.add(new_item)
                db.commit()
                db.refresh(new_item)
                return new_item
            except IntegrityError:
                db.rollback()
                raise HTTPException(409, "Duplicate item")

    Performance Note:
        Sessions use connection pooling under the hood.
        Creating a session doesn't open a new TCP connection;
        it borrows one from the pool and returns it on close.
    """
    try:
        # Create new session from factory
        db = SessionLocal()

        # Yield session to route handler
        # Execution pauses here until request is complete
        yield db

    finally:
        # Always close session, even if exception occurred
        # This returns the connection to the pool
        db.close()


# =============================================================================
# Future Dependencies (Template)
# =============================================================================

# def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ) -> User:
#     """
#     Authenticate and return current user from JWT token.
#
#     Args:
#         token: JWT bearer token from Authorization header
#         db: Database session for user lookup
#
#     Returns:
#         User object for authenticated user
#
#     Raises:
#         HTTPException 401: Invalid or expired token
#     """
#     pass


# def get_redis() -> Generator:
#     """
#     Provide Redis connection for caching.
#
#     Yields:
#         Redis client connection
#     """
#     pass
