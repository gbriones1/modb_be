"""
This example demonstrates pydantic serialisation
"""
from tortoise import Tortoise, fields, run_async
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.contrib.pydantic import pydantic_queryset_creator
from tortoise.contrib.pydantic.base import _get_fetch_fields
from tortoise.models import Model


class User(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)
    hashed_password = fields.CharField(max_length=128)
    # roles: fields.ManyToManyRelation["Role"] = fields.ManyToManyField(
    #     "models.Role", related_name="users", through="user_role"
    # )
    # roles = fields.ManyToManyField("models.Role")
    roles: fields.ManyToManyRelation["Role"] = fields.ManyToManyField("models.Role")

    class Meta:
        ordering = ["name"]


class Role(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    # users: fields.ManyToManyRelation[User] = fields.ManyToManyField(
    #     "models.User", related_name="roles", through="user_roles"
    # )

    class Meta:
        ordering = ["name"]


async def run():
    await Tortoise.init(db_url="sqlite://:memory:", modules={"models": ["__main__"]})
    await Tortoise.generate_schemas()

    User_Pydantic = pydantic_model_creator(User)
    User_Pydantic_List = pydantic_queryset_creator(User)
    Role_Pydantic = pydantic_model_creator(Role)

    await User.create(name="Empty", hashed_password="x")
    event = await User.create(name="Test", hashed_password="x")
    event2 = await User.create(name="TestLast", hashed_password="x")
    event3 = await User.create(name="Test2", hashed_password="x")
    team1 = await Role.create(name="Onesies")
    team2 = await Role.create(name="T-Shirts")
    team3 = await Role.create(name="Alternates")
    await event.roles.add(team1, team2, team3)
    await event2.roles.add(team1, team2)
    await event3.roles.add(team1, team3)

    p = await User_Pydantic.from_tortoise_orm(await User.get(name="Test"))

    print("One User:", p.json(indent=4))
    ff = _get_fetch_fields(User_Pydantic, User)

    values = await User.all().prefetch_related(*ff)

    role = await Role.get(name="Onesies")
    import pdb; pdb.set_trace()

    pl = await User_Pydantic_List.from_queryset(User.all())
    # print("All Users", pl.json(indent=4))


if __name__ == "__main__":
    run_async(run())