from tortoise import Tortoise, fields, models, run_async
from tortoise.contrib.pydantic import pydantic_model_creator

from main.api.auth.models import User, Role
# from api.auth.schemas import User_Pydantic, UserIn_Pydantic
from main.api.auth.schemas import UserSchema

# class User(models.Model):

#     id = fields.IntField(pk=True)
#     username = fields.CharField(max_length=20, unique=True)
#     full_name = fields.CharField(max_length=50, null=True)
#     hashed_password = fields.CharField(max_length=128)
#     created_at = fields.DatetimeField(auto_now_add=True)
#     modified_at = fields.DatetimeField(auto_now=True)
#     active = fields.BooleanField(default=True)
#     roles: fields.ManyToManyRelation["Role"] = fields.ManyToManyField("models.Role")


#     class Meta:
#         ordering = ["username"]


# class Role(models.Model):
#     id = fields.IntField(pk=True)
#     name = fields.TextField()

#     class Meta:
#         ordering = ["name"]

# Tortoise.init_models(["api.auth.models"], "models")
# Tortoise.generate_schemas()
# User_Pydantic = pydantic_model_creator(User)

async def run():
    await Tortoise.init(db_url="sqlite://:memory:", modules={"models": ["api.auth.models"]})
    await Tortoise.generate_schemas()


    u = await User.create(username="a", hashed_password="a")
    r = await Role.create(name="x")

    await u.roles.add(r)
    
    u2 = await User.get(id=1)
    # import pdb; pdb.set_trace()

    p = await UserSchema.from_async_orm(u2)
    print("One User:", p.json(indent=4))

    # print(UserIn_Pydantic.schema())



if __name__ == "__main__":
    run_async(run())