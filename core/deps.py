"""FastAPI dependency providers (database sessions, etc.)."""

from collections.abc import Generator

from database.session import SessionLocal


def get_db() -> Generator:
    """Yield a SQLAlchemy session, closing it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
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
