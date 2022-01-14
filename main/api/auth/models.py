from typing import Any, List
from passlib.context import CryptContext
from tortoise import Tortoise, fields, models

from main.api.auth.errors import LoginException


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


class User(models.Model):

    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=20, unique=True)
    full_name = fields.CharField(max_length=50, null=True)
    hashed_password = fields.CharField(max_length=128)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)
    active = fields.BooleanField(default=True)
    is_admin = fields.BooleanField(default=False)
    roles: fields.ManyToManyRelation["Role"] = fields.ManyToManyField("models.Role", related_name="users")

    class Meta:
        ordering = ["username"]

    @classmethod
    def create(self, **data: Any) -> models.Model:
        data["hashed_password"] = get_password_hash(data.get("password"))
        return super().create(**data)

    def authenticate(self, password: str) -> models.Model:
        if verify_password(password, self.hashed_password):
            return self
        raise LoginException

    async def get_role_ids(self) -> List[int]:
        await self.fetch_related("roles")
        role_ids = []
        for role in self.roles.related_objects:
            role_ids.append(role.id)
        return role_ids



class Role(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name"]


Tortoise.init_models(["main.api.auth.models"], "models")
