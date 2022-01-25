import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Awesome API"
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    hash_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    # db_url: str = "sqlite://./dev.sqlite3"
    db_url: str = "postgres://postgres:mysecretpassword@172.17.0.2:5432/somedb"
    db_generate: bool = True
    admin_username: str = "user"
    admin_password: str = "secret"
    allow_origin: str = "http://localhost"

class TestSettings(BaseSettings):
    app_name: str = "Awesome API"
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    hash_algorithm: str = "HS256"
    access_token_expire_minutes: int = 5
    db_url: str = "sqlite://./test.sqlite3"
    db_generate: bool = True
    # db_url: str = "sqlite://:memory:"
    admin_username: str = "user"
    admin_password: str = "secret"
    allow_origin: str = "http://localhost"

settings = Settings()
if os.getenv('ENVIRONMENT') == "testing":
    settings = TestSettings()

TORTOISE_ORM = {
    "connections": {"default": settings.db_url},
    "apps": {
        "models": {
            "models": ["main.api.auth.models", "main.api.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}