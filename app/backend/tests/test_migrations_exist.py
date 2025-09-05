import os


def test_initial_migration_exists() -> None:
    path = os.path.join(
        os.path.dirname(__file__), "..", "alembic", "versions", "0001_initial.py"
    )
    path = os.path.abspath(path)
    assert os.path.exists(path), f"Migration not found: {path}"




