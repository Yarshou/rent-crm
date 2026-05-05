from re import compile
from typing import Annotated

from pydantic import AfterValidator, Field

__all__ = ["EmailStr", "PasswordStr", "UsernameStr"]

PASSWORD_PATTERN = compile(pattern=r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]?).{8,64}$")
EMAIL_PATTERN = compile(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_password(value: str) -> str:
    if PASSWORD_PATTERN.fullmatch(string=value) is None:
        raise ValueError("the password must contain a large letter and a number")
    return value


def validate_email(value: str) -> str:
    if EMAIL_PATTERN.fullmatch(string=value) is None:
        raise ValueError("invalid email address")
    return value


def validate_username(value: str) -> str:
    if not value.isidentifier():
        raise ValueError(
            "username can consist only of letters, numbers and underscores, starting with a letter or an underscore"
        )
    return value


EmailStr = Annotated[str, AfterValidator(func=validate_email), Field(min_length=6, max_length=320)]
PasswordStr = Annotated[str, AfterValidator(func=validate_password)]
UsernameStr = Annotated[str, AfterValidator(func=validate_username), Field(min_length=2, max_length=32)]
