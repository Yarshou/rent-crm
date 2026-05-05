import base64
import binascii
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from re import fullmatch

from config.settings import settings
from fastapi import HTTPException, status
from pydantic import ValidationError
from schemas.auth import TokenPayload
from schemas.users import UserDTO

__all__ = [
    "create_access_token",
    "create_password_hash",
    "create_refresh_token",
    "decode_access_token",
    "get_access_token_expire_delta",
    "get_refresh_token_expire_delta",
    "get_unauthorized_exception",
    "verify_password",
]

_TOKEN_TYPE = "JWT"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 64


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _get_secret_key() -> str:
    return settings.JWT_ACCESS_SECRET_KEY.get_secret_value()


def _get_expire_delta(value: str, setting_name: str) -> timedelta:
    match = fullmatch(r"(?P<value>\d+)(?P<unit>[smhd])", value.strip())
    if match is None:
        raise ValueError(f"{setting_name} must match '<value><unit>', e.g. '15m'.")

    delta_value = int(match.group("value"))
    return {
        "s": timedelta(seconds=delta_value),
        "m": timedelta(minutes=delta_value),
        "h": timedelta(hours=delta_value),
        "d": timedelta(days=delta_value),
    }[match.group("unit")]


def get_access_token_expire_delta() -> timedelta:
    return _get_expire_delta(settings.JWT_ACCESS_EXPIRE, "JWT_ACCESS_EXPIRE")


def get_refresh_token_expire_delta() -> timedelta:
    return _get_expire_delta(settings.JWT_REFRESH_EXPIRE, "JWT_REFRESH_EXPIRE")


def create_password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${_base64url_encode(salt)}${_base64url_encode(password_hash)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, n, r, p, salt, password_digest = password_hash.split("$", maxsplit=5)
    except ValueError as exception:
        raise ValueError("Invalid password hash format.") from exception

    if algorithm != "scrypt":
        raise ValueError("Unsupported password hash algorithm.")

    computed_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=_base64url_decode(salt),
        n=int(n),
        r=int(r),
        p=int(p),
        dklen=_SCRYPT_DKLEN,
    )
    return hmac.compare_digest(_base64url_encode(computed_hash), password_digest)


def _get_user_role(user: UserDTO) -> str:
    return "super_admin" if user.is_super_admin else "user"


def _create_token(*, user: UserDTO, algorithm: str, expires_delta: timedelta, token_type: str) -> str:
    if algorithm != "HS256":
        raise ValueError("Only HS256 is supported for JWT tokens.")

    expires_at = datetime.now(tz=UTC) + expires_delta
    payload = {
        "sub": str(user.id),
        "role": _get_user_role(user),
        "type": token_type,
        "exp": int(expires_at.timestamp()),
    }
    header = {"alg": algorithm, "typ": _TOKEN_TYPE}
    header_segment = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode()
    signature = hmac.new(_get_secret_key().encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_segment}.{payload_segment}.{_base64url_encode(signature)}"


def create_access_token(user: UserDTO) -> str:
    return _create_token(
        user=user,
        algorithm=settings.JWT_ACCESS_ALGORITHM,
        expires_delta=get_access_token_expire_delta(),
        token_type="access",
    )


def create_refresh_token(user: UserDTO) -> str:
    return _create_token(
        user=user,
        algorithm=settings.JWT_REFRESH_ALGORITHM,
        expires_delta=get_refresh_token_expire_delta(),
        token_type="refresh",
    )


def decode_access_token(token: str) -> TokenPayload:
    if settings.JWT_ACCESS_ALGORITHM != "HS256":
        raise ValueError("Only HS256 is supported for JWT access tokens.")

    try:
        header_segment, payload_segment, signature_segment = token.split(".", maxsplit=2)
    except ValueError as exception:
        raise get_unauthorized_exception() from exception

    signing_input = f"{header_segment}.{payload_segment}".encode()
    expected_signature = hmac.new(_get_secret_key().encode("utf-8"), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(_base64url_encode(expected_signature), signature_segment):
        raise get_unauthorized_exception()

    try:
        header = json.loads(_base64url_decode(header_segment))
        payload = json.loads(_base64url_decode(payload_segment))
        token_payload = TokenPayload.model_validate(payload)
    except (binascii.Error, json.JSONDecodeError, ValidationError, ValueError) as exception:
        raise get_unauthorized_exception() from exception

    if header.get("alg") != settings.JWT_ACCESS_ALGORITHM or header.get("typ") != _TOKEN_TYPE:
        raise get_unauthorized_exception()

    if token_payload.type != "access":
        raise get_unauthorized_exception()

    if datetime.now(tz=UTC).timestamp() >= token_payload.exp:
        raise get_unauthorized_exception()

    return token_payload


def get_unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
