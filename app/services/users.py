from dataclasses import dataclass

@dataclass
class User:
    id: str
    username: str
    role: str = "user"

# Base de usuarios en memoria (demo)
_USERS = {
    "userprueba1": {"password": "userprueba1", "id": "u-001", "role": "admin"},
}

def verify_user(username: str, password: str) -> User | None:
    u = _USERS.get(username)
    if not u:
        return None
    if password != u["password"]:
        return None
    return User(id=u["id"], username=username, role=u["role"])
