from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

class Extension(Base):
    __tablename__ = "extensions"

    # --- Mandatory Fields ---
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Indexed 'name' and 'publisher' for faster search performance
    name = Column(String, nullable=False, index=True)
    publisher = Column(String, nullable=False, index=True)

    # JSONB is best for key-value pairs like {'vscode': '^1.95.0'}
    engines = Column(JSONB, nullable=False)

    # --- Optional Fields ---
    license = Column(String, nullable=True)
    displayName = Column(String, nullable=True)

    # Using 'Text' instead of 'String' because descriptions can be long
    description = Column(Text, nullable=True)

    # Simple arrays for tags and categories
    categories = Column(ARRAY(String), nullable=True)
    keywords = Column(ARRAY(String), nullable=True)

    galleryBanner = Column(JSONB, nullable=True)
    preview = Column(Boolean, nullable=True)

    # Changed to JSONB because badges are usually objects (e.g., {url, href, description})
    badges = Column(JSONB, nullable=True)

    # 'Text' is required here; README files (markdown) can be very large
    markdown = Column(Text, nullable=True)

    # JSONB allows flexibility (can be a Boolean 'false', a String 'url', or a Dict)
    qna = Column(JSONB, nullable=True)

    sponsor = Column(JSONB, nullable=True)
    icon = Column(String, nullable=True)
    pricing = Column(String, nullable=True)

    # Entry points for the extension
    main = Column(String, nullable=True)
    web = Column(String, nullable=True)

    # --- Metadata / Timestamps ---
    # Automatically tracks when the record was created or updated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- Constraints ---
    # Ensures data integrity: A publisher cannot have two extensions with the exact same name
    __table_args__ = (
        UniqueConstraint('publisher', 'name', name='uix_publisher_name'),
    )
