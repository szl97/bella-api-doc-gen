import pytest

from app.core.security import hash_token, verify_token


@pytest.mark.unit
class TestSecurity:
    """Test cases for security functions."""

    def test_hash_token_consistent(self):
        """Test that hashing the same token produces the same hash."""
        token = "test-token-123"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64-character hex string

    def test_hash_token_different_inputs(self):
        """Test that different tokens produce different hashes."""
        token1 = "token1"
        token2 = "token2"
        
        hash1 = hash_token(token1)
        hash2 = hash_token(token2)
        
        assert hash1 != hash2

    def test_hash_token_empty_string(self):
        """Test hashing empty string."""
        empty_hash = hash_token("")
        
        assert len(empty_hash) == 64
        assert empty_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_verify_token_success(self):
        """Test successful token verification."""
        plain_token = "my-secret-token"
        hashed_token = hash_token(plain_token)
        
        assert verify_token(plain_token, hashed_token) is True

    def test_verify_token_failure(self):
        """Test failed token verification."""
        plain_token = "my-secret-token"
        wrong_token = "wrong-token"
        hashed_token = hash_token(plain_token)
        
        assert verify_token(wrong_token, hashed_token) is False

    def test_verify_token_empty_strings(self):
        """Test token verification with empty strings."""
        assert verify_token("", hash_token("")) is True
        assert verify_token("", hash_token("not-empty")) is False
        assert verify_token("not-empty", hash_token("")) is False

    def test_hash_token_unicode(self):
        """Test hashing tokens with unicode characters."""
        unicode_token = "测试令牌🔐"
        hashed = hash_token(unicode_token)
        
        assert len(hashed) == 64
        assert verify_token(unicode_token, hashed) is True

    def test_hash_token_special_characters(self):
        """Test hashing tokens with special characters."""
        special_token = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = hash_token(special_token)
        
        assert len(hashed) == 64
        assert verify_token(special_token, hashed) is True