import jwt
import os
import hashlib
import base64
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from mementonos.utils.logger import get_logger

logger = get_logger(__name__)
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 14

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_jwt(user_id: int, pair_id: Optional[int] = None) -> str:
    payload = {
        "sub": str(user_id),
        "pair": str(pair_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str) -> dict:
    if not token:
        logger.info("decode_jwt: token is empty")
        return {}
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info("decode_jwt SUCCESS: payload = %s", payload)
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("decode_jwt: ExpiredSignatureError")
        return {}
    except jwt.InvalidSignatureError:
        logger.warning("decode_jwt: InvalidSignatureError - WRONG SECRET_KEY?")
        return {}
    except jwt.InvalidTokenError as e:
        logger.warning("decode_jwt: InvalidTokenError %s", str(e))
        return {}
    except Exception as e:
        logger.warning("decode_jwt: UNEXPECTED ERROR %s", type(e).__name__, str(e))
        return {}

def derive_fernet_key(password: str, salt: bytes, iterations: int = 10_000) -> bytes:
    """PBKDF2 → 32 байта → base64 для Fernet"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key

def encrypt_master_key(master_key: bytes, password: str, salt: bytes) -> bytes:
    fernet_key = derive_fernet_key(password, salt)
    f = Fernet(fernet_key)
    return f.encrypt(master_key)

def decrypt_master_key(encrypted: bytes, password: str, salt: bytes) -> bytes:
    fernet_key = derive_fernet_key(password, salt)
    f = Fernet(fernet_key)
    try:
        return f.decrypt(encrypted)
    except InvalidToken:
        logger.warning("Wrong password provided.")