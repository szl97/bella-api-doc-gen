import hashlib
from fastapi.security import OAuth2PasswordBearer

def hash_token(token: str) -> str:
    """
    Hashes a token using SHA256.
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def verify_token(plain_token: str, hashed_token: str) -> bool:
    """
    Verifies a plain token against a stored SHA256 hash.
    """
    return hash_token(plain_token) == hashed_token

# tokenUrl is a dummy value as we are not implementing a token issuing endpoint.
# This is used by FastAPI to parse Bearer tokens from the Authorization header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/api-doc/dummy-token-url") # Using a path within our API prefix for consistency.
