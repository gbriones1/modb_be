from tortoise.exceptions import IntegrityError

from main.api.auth.models import Role, User
from main.logger import logger

ROLE_STORAGE = "Almacen"
ROLE_STORAGE_BOSS = "Jefe de almacen"
ROLE_BUYER = "Compras"
ROLE_WORK_BOSS = "Jefe de taller"

ALL_ROLES = [
    ROLE_STORAGE,
    ROLE_STORAGE_BOSS,
    ROLE_BUYER,
    ROLE_WORK_BOSS,
]

ENDPOINT_PERMS = {
    ROLE_STORAGE: [
        "create_input",
        "update_input",
        "delete_input",
    ]
}

async def generate_roles() -> None:
    for r in ALL_ROLES:
        try:
            logger.debug(f"Generating role {r}")
            await Role.create(name=r)
        except IntegrityError:
            logger.debug(f"Role {r} already exists")

async def generate_superuser(username: str, password: str) -> None:
    try:
        logger.debug(f"Generating superuser {username}")
        await User.create(username=username, password=password, is_admin=True)
    except IntegrityError:
        logger.debug(f"Superuser already exists")
