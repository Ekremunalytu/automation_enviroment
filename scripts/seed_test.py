"""
scripts/seed_test.py
====================

Database Seeding Script for Development and Testing
----------------------------------------------------

This script populates the database with sample VS Code extension data
for development and testing purposes. It creates a realistic test record
that exercises all model fields.

Purpose:
    - Quick database population for development
    - Testing CRUD operations with known data
    - Verifying schema/model compatibility
    - API endpoint testing

Usage:
    From project root:
        python scripts/seed_test.py
    
    Or with Docker:
        docker-compose exec api python scripts/seed_test.py

Prerequisites:
    - Database must be running (Docker Compose up)
    - Migrations must be applied (alembic upgrade head)
    - .env file must be configured with DATABASE_URL

Sample Data:
    Creates a single extension record based on Microsoft's Python extension,
    with all fields populated to test the full schema.

Notes:
    - Running multiple times will fail due to unique constraint
    - Use for initial seeding or after database reset
    - For production, create a proper migration or backup restore

Future Enhancements:
    - Add --force flag to delete existing and recreate
    - Add multiple sample extensions
    - Add random data generation for stress testing
"""

import sys
import os

# =============================================================================
# Path Configuration
# =============================================================================

# Add project root to Python path
# This is necessary because we're running from scripts/ subdirectory
# but need to import from project root modules
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from database.session import SessionLocal
from models.models import Extension


def seed_test_data():
    """
    Insert a sample VS Code extension into the database.
    
    Creates a comprehensive test record with all model fields populated.
    This demonstrates the full capability of the Extension model and
    provides known data for API testing.
    
    Process:
        1. Create database session
        2. Create Extension ORM object with test data
        3. Add to session and commit
        4. Refresh to get auto-generated fields (id, created_at)
        5. Print success/failure message
        6. Clean up session
    
    Test Data Details:
        The sample is based on Microsoft's Python extension, which is
        one of the most popular VS Code extensions. Fields are:
        
        Required:
            - name: "python"
            - publisher: "ms-python"
            - engines: {"vscode": "^1.95.0"}
        
        Optional (all populated):
            - license, displayName, description
            - categories, keywords (arrays)
            - galleryBanner, badges, sponsor (JSONB)
            - preview (boolean)
            - markdown, qna, icon, pricing, main, web (strings)
    
    Error Handling:
        - IntegrityError (duplicate): Caught, rolled back, logged
        - Other exceptions: Caught, rolled back, logged
        - Session always closed in finally block
    
    Returns:
        None: Prints status messages to stdout
    
    Example Output:
        ✅ Test record added! ID: 1
           Name: python
           Publisher: ms-python
    
        OR on duplicate:
        ❌ Error: UNIQUE constraint failed: extensions.publisher, extensions.name
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # =================================================================
        # Create Sample Extension Object
        # =================================================================
        
        # Sample VS Code extension data with all fields populated
        # Based on real Microsoft Python extension manifest
        test_extension = Extension(
            
            # ---------------------------------------------------------
            # Required Fields
            # These must be present in every extension's package.json
            # ---------------------------------------------------------
            
            name="python",
            """Extension identifier (unique per publisher)"""
            
            publisher="ms-python",
            """Publisher account name"""
            
            engines={"vscode": "^1.95.0"},
            """
            VS Code version requirements.
            ^1.95.0 means version 1.95.0 or any compatible higher version.
            """
            
            # ---------------------------------------------------------
            # Optional Fields - All Populated for Testing
            # These fields demonstrate all model capabilities
            # ---------------------------------------------------------
            
            license="MIT",
            """SPDX license identifier"""
            
            displayName="Python",
            """Human-readable name shown in VS Code UI"""
            
            description="IntelliSense, linting, debugging, code navigation, "
                       "code formatting, refactoring, and more for Python.",
            """Extension description for marketplace listing"""
            
            categories=["Programming Languages", "Linters", "Debuggers", "Formatters"],
            """Marketplace category tags (PostgreSQL ARRAY)"""
            
            keywords=["python", "django", "flask", "pylint", "autopep8"],
            """Search keywords for marketplace discovery (PostgreSQL ARRAY)"""
            
            galleryBanner={
                "color": "#1e415e",
                "theme": "dark"
            },
            """Marketplace banner styling (PostgreSQL JSONB)"""
            
            preview=False,
            """Not a preview/beta release"""
            
            badges=[
                {
                    "url": "https://img.shields.io/badge/build-passing-brightgreen",
                    "href": "https://github.com/microsoft/vscode-python",
                    "description": "Build Status"
                }
            ],
            """Status badges displayed on marketplace page (PostgreSQL JSONB)"""
            
            markdown="github",
            """Use GitHub Flavored Markdown for rendering"""
            
            qna="marketplace",
            """
            Q&A configuration - uses marketplace Q&A system.
            Can also be: False (disabled), URL string, or config object.
            """
            
            sponsor={
                "url": "https://github.com/sponsors/microsoft"
            },
            """Sponsor/donation link configuration (PostgreSQL JSONB)"""
            
            icon="https://ms-python.gallerycdn.vsassets.io/extensions/ms-python/python/icon.png",
            """URL to extension icon"""
            
            pricing="Free",
            """Pricing tier: Free, Trial, or Paid"""
            
            main="./dist/extension.js",
            """Desktop extension entry point (Node.js)"""
            
            web="./dist/web-extension.js",
            """Web extension entry point (browser/vscode.dev)"""
        )
        
        # =================================================================
        # Database Operations
        # =================================================================
        
        # Stage the extension for insertion
        db.add(test_extension)
        
        # Commit the transaction (writes to database)
        db.commit()
        
        # Refresh to load auto-generated values (id, created_at)
        db.refresh(test_extension)
        
        # Success output
        print(f"✅ Test record added! ID: {test_extension.id}")
        print(f"   Name: {test_extension.name}")
        print(f"   Publisher: {test_extension.publisher}")
        
    except Exception as e:
        # Handle any errors (duplicate entry, connection issues, etc.)
        db.rollback()  # Discard pending changes
        print(f"❌ Error: {e}")
        
    finally:
        # Always close the session to return connection to pool
        db.close()


# =============================================================================
# Script Entry Point
# =============================================================================

if __name__ == "__main__":
    """
    Script entry point when run directly.
    
    Usage:
        python scripts/seed_test.py
    
    This block only executes when the script is run directly,
    not when imported as a module.
    """
    seed_test_data()
