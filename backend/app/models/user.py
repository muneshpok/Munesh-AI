from dataclasses import dataclass


@dataclass(slots=True)
class User:
    email: str
    password_hash: str
