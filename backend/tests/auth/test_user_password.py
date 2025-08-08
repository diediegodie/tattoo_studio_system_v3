"""
Unit, edge, and failure tests for User model password methods.
"""

import pytest
from backend.models.user import User


class TestUserPassword:
    def test_set_password_hashes_password(self):
        user = User(name="Test", email="test@example.com")
        user.set_password("secure123")
        hash_val = user.password_hash
        assert isinstance(hash_val, str)
        assert hash_val != "secure123"
        assert (
            hash_val.startswith("$2b$")
            or hash_val.startswith("$2a$")
            or hash_val.startswith("$2y$")
        )

    def test_check_password_success(self):
        user = User(name="Test", email="test@example.com")
        user.set_password("mypassword")
        assert user.check_password("mypassword") is True

    def test_check_password_failure(self):
        user = User(name="Test", email="test@example.com")
        user.set_password("rightpass")
        assert user.check_password("wrongpass") is False

    def test_check_password_with_empty_string(self):
        user = User(name="Test", email="test@example.com")
        user.set_password("")
        assert user.check_password("") is True
        assert user.check_password("notempty") is False

    def test_set_password_overwrites_previous_hash(self):
        user = User(name="Test", email="test@example.com")
        user.set_password("first")
        first_hash = user.password_hash
        user.set_password("second")
        second_hash = user.password_hash
        assert isinstance(second_hash, str)
        assert second_hash != first_hash
        assert user.check_password("second") is True
        assert user.check_password("first") is False

    def test_check_password_with_non_string_hash(self):
        user = User(name="Test", email="test@example.com")
        # Simulate legacy/bad data by setting password_hash to a non-string value using __dict__
        user.__dict__["password_hash"] = 123456
        with pytest.raises(Exception):
            user.check_password("any")
