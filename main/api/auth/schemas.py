from datetime import timedelta
from typing import Dict, List, Optional
from pydantic.main import BaseModel
from tortoise.contrib.pydantic.base import PydanticModel#, _get_fetch_fields
from tortoise.queryset import QuerySet, QuerySetSingle

from main.api.auth.models import User, Role


class TokenSchema(BaseModel):
    access_token: str
    token_type: str
    expires_on: Optional[timedelta]


class TokenDataSchema(BaseModel):
    username: str
    roles: List[int]
    is_admin: bool



class AsyncBaseSchema(PydanticModel):

    @classmethod
    async def from_async_orm(cls, obj) -> "PydanticModel":
        # Get fields needed to fetch
        # fetch_fields = _get_fetch_fields(cls, getattr(cls.__config__, "orig_model"))
        fetch_fields = getattr(cls.__config__, "fetch_fields", [])
        
        # Fetch fields
        await obj.fetch_related(*fetch_fields)
        # Convert to pydantic object
        values = super().from_orm(obj)
        return values
        
    @classmethod
    async def from_queryset_single(cls, queryset: "QuerySetSingle") -> "PydanticModel":
        # fetch_fields = _get_fetch_fields(cls, getattr(cls.__config__, "orig_model"))
        fetch_fields = getattr(cls.__config__, "fetch_fields", [])
        return cls.from_orm(await queryset.prefetch_related(*fetch_fields))

    @classmethod
    async def from_queryset(cls, queryset: "QuerySet") -> "List[PydanticModel]":
        # fetch_fields = _get_fetch_fields(cls, getattr(cls.__config__, "orig_model"))
        fetch_fields = getattr(cls.__config__, "fetch_fields", [])
        return [cls.from_orm(e) for e in await queryset.prefetch_related(*fetch_fields)]


class RoleBaseSchema(AsyncBaseSchema):
    name: str

    class Config:
        orig_model = Role


class RoleSchema(RoleBaseSchema):
    id: int


class UserBaseSchema(AsyncBaseSchema):
    username: str
    full_name: Optional[str]
    active: Optional[bool]
    is_admin: Optional[bool]
    # role_names: Optional[List[RoleBaseSchema]]
    roles: Optional[List[RoleBaseSchema]]

    # @classmethod
    # def validate(cls, **data):
    #     print("custom validate")
    #     return super(UserBaseSchema, cls).validate(**data)
    
    # @root_validator(pre=True)
    # def pre_validator(cls, v):
    #     # print(f"custom val: {v}")
    #     import pdb; pdb.set_trace()
    #     return v

    # @root_validator()
    # def post_validator(cls, v):
    #     print(f"custom val: {v}")
    #     # import pdb; pdb.set_trace()
    #     return v

    # @classmethod
    # def from_orm(cls, *args, **data):
    #     # import pdb; pdb.set_trace()
    #     result = super(UserBaseSchema, cls).from_orm(*args, **data)
    #     return result

    class Config:
        orig_model = User
        fetch_fields = ('roles', )
    #     arbitrary_types_allowed = True

class UserSchema(UserBaseSchema):
    id: int
    
    class Config:
        orm_mode = True

class UserCreateSchema(UserBaseSchema):
    password: str