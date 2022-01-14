import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from main.api.auth.permissions import generate_roles, generate_superuser
from main.api.auth.routes import router as auth_router
from main.api.routes import router
from main.settings import settings
from main.logger import logger

# logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(name)s %(message)s')

app = FastAPI()
app.include_router(auth_router)
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.17",
        "http://172.17.0.1",
        "http://localhost"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


register_tortoise(
    app,
    db_url=settings.db_url,
    modules={"models": ["main.api.auth.models", "main.api.models"]},
    generate_schemas=settings.db_generate,
    add_exception_handlers=True,
)

@app.on_event("startup")
async def startup_event():
    logger.debug("Start up")
    await generate_roles()
    if settings.admin_username and settings.admin_password:
        await generate_superuser(settings.admin_username, settings.admin_password)

@app.on_event("shutdown")
async def shutdown_event():
    logger.debug("Shutdown")
    await Tortoise.close_connections()


@app.get("/")
def root(request: Request):
    # import pdb; pdb.set_trace()
    return {"message": "Hello World"}
