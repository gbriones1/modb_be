from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import Request, Depends
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError

from main.api.auth.errors import LoginException, PermException
from main.api.auth.models import User
from main.api.auth.schemas import TokenDataSchema, UserSchema
from main.settings import settings
from main.logger import logger


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.hash_algorithm)
    return encoded_jwt


async def requires_login(request: Request, token: str = Depends(oauth2_scheme)) -> UserSchema:
    # logger.debug(dir(request))
    # logger.debug(await request.body())
    # logger.debug(await request.form())
    # logger.debug(await request.json())
    # logger.debug(request.headers)
    logger.debug(f"Validating login with token {token}")
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.hash_algorithm])
        username: str = payload.get("username")
        roles: List[int] = payload.get("roles")
        is_admin: bool = payload.get("is_admin")
        if username is None:
            raise LoginException
        token_data = TokenDataSchema(username=username, roles=roles, is_admin=is_admin)
    except JWTError:
        raise LoginException
    user = await User.get(username=token_data.username)
    if user is None:
        raise LoginException
    logger.debug(f"Validated user: {user.username}")
    return await UserSchema.from_async_orm(user)


async def requires_permission(request: Request, current_user: UserSchema = Depends(requires_login)) -> UserSchema:
    endpoint = request.scope.get('endpoint').__name__
    logger.debug(f"Validating permissions to {endpoint} for user: {current_user.username}")
    if not current_user.active:
        raise PermException
    if current_user.is_admin:
        logger.debug(f"User {current_user.username} is admin")
        return current_user
    raise PermException


def requires_perm(permission=None):
    def decorator(f):
        async def decorated_function(request, *args, **kwargs):
            print(f, permission)
            response = await f(request, *args, **kwargs)
            return response

        return decorated_function

    return decorator

