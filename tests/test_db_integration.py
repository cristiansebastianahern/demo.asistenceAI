# tests/test_db_integration.py
"""Integration tests for the Nexa hospital system.

These tests use a real PostgreSQL database (no mocks) and verify that the
`AdminRepository` can read users and perform CRUD operations on the
`edificios` table.

The repository and the SQLAlchemy engine are imported from the project's
infrastructure package.
"""

import pytest
from sqlalchemy import text

# Import the repository and the global engine
from src.infrastructure.admin_repository import AdminRepository
from src.infrastructure.database import engine


@pytest.fixture(scope="function")
def admin_repo():
    """Provide a real AdminRepository instance.

    The fixture yields the repository and ensures that any test data created
    during the test is cleaned up afterwards.
    """
    repo = AdminRepository()
    yield repo
    # Cleanup is handled in individual tests where needed.


def test_read_users_real_db(admin_repo):
    """Smoke test: ensure we can read users from the real DB.

    The test asserts that the returned list is not empty and that the admin
    user exists with the expected email address.
    """
    users = admin_repo.get_users()
    assert users, "The users list should not be empty"
    # Find the admin user (assuming a role or username field identifies it)
    admin_user = next((u for u in users if getattr(u, "username", "") == "admin"), None)
    assert admin_user is not None, "Admin user should be present"
    assert getattr(admin_user, "email", None) == "admin@nexa.com", "Admin email should match expected value"


def test_create_and_read_edificio(admin_repo):
    """CRUD lifecycle test for the `edificios` entity.

    Inserts a test building, verifies its presence, and then removes it to
    avoid leaving stray data in the production database.
    """
    building_name = "Edificio QA Test"
    building_code = "QA-101"

    # Insert the building
    admin_repo.save_edificio(building_name, building_code)

    try:
        edificios = admin_repo.get_edificios()
        # Verify the newly inserted building exists
        matching = [e for e in edificios if getattr(e, "nombre", "") == building_name]
        assert matching, f"Building '{building_name}' should be present after insertion"
    finally:
        # Cleanup: delete the test building directly via raw SQL
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM edificios WHERE nombre = :name AND codigo = :code"),
                {"name": building_name, "code": building_code},
            )
