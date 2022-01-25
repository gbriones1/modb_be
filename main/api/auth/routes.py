from datetime import timedelta
from typing import List, Optional
from fastapi import Depends, APIRouter, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import DoesNotExist

from main.api.auth.models import User, Role
from main.api.auth.schemas import TokenSchema, UserSchema, UserCreateSchema, RoleSchema
from main.api.auth.errors import UserNotFoundException, LoginException
from main.api.auth.dependencies import create_access_token, requires_login, requires_permission
from main.api.schemas import StatusSchema
from main.settings import settings
from main.logger import logger


router = APIRouter()


@router.post("/token", response_model=TokenSchema)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), rememberme: Optional[bool] = Body(default=False) ):
    logger.debug(f"Generating token for user; {form_data.username}")
    user = None
    try:
        user = await User.get(username=form_data.username)
    except DoesNotExist as e:
        raise LoginException
    user.authenticate(form_data.password)
    expires_delta = None
    if not rememberme:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"username": user.username, "roles": await user.get_role_ids(), "is_admin": user.is_admin}, expires_delta=expires_delta
    )
    return {"access_token": access_token, "token_type": "bearer", "expires_on": expires_delta}


@router.get("/user", response_model=List[UserSchema])
async def list_users(current_user: UserSchema = Depends(requires_permission)):
    result = await UserSchema.from_queryset(User.all())
    return result


@router.post("/user", response_model=UserSchema)
async def create_user(user: UserCreateSchema, current_user: UserSchema = Depends(requires_permission)):
    data = user.dict(exclude_unset=True)
    roles_data = data.pop("roles", [])
    user_obj = await User.create(**data)
    for role_data in roles_data:
        role = await Role.get(name=role_data.get("name"))
        await user_obj.roles.add(role)
    await user_obj.save()
    return await UserSchema.from_async_orm(user_obj)


@router.get(
    "/user/{user_id}", response_model=UserSchema, responses={404: {"model": HTTPNotFoundError}}
)
async def get_user(user_id: int, current_user: UserSchema = Depends(requires_permission)):
    return await UserSchema.from_queryset_single(User.get(id=user_id))


@router.put(
    "/user/{user_id}", response_model=UserSchema, responses={404: {"model": HTTPNotFoundError}}
)
async def update_user(user_id: int, user: UserCreateSchema, current_user: UserSchema = Depends(requires_permission)):
    data = user.dict(exclude_unset=True)
    # data["hashed_password"] = get_password_hash(data.pop("password"))
    updated_count = await User.filter(id=user_id).update(**data)
    if not updated_count:
        raise UserNotFoundException
    return await UserSchema.from_queryset_single(User.get(id=user_id))


@router.delete("/user/{user_id}", response_model=StatusSchema, responses={404: {"model": HTTPNotFoundError}})
async def delete_user(user_id: int, current_user: UserSchema = Depends(requires_permission)):
    deleted_count = await User.filter(id=user_id).delete()
    if not deleted_count:
        raise UserNotFoundException
    return StatusSchema(message=f"Deleted user {user_id}")


@router.get("/user/me/", response_model=UserSchema)
async def read_users_me(current_user: UserSchema = Depends(requires_login)):
    return current_user


@router.get("/role", response_model=List[RoleSchema])
async def list_roles():
    return await RoleSchema.from_queryset(Role.all())
