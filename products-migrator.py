import asyncio
from datetime import datetime

import tortoise
from tortoise import Tortoise

from main.api.schemas import ApplianceSerializer, BrandSerializer, ProductSerializer, ProviderSerializer
from main.settings import settings

dry_run = False

def isfloat(value):
    try:
        float(value)
    except:
        return False
    return True

async def get_all(serializer):
    model = serializer.__config__.orig_model
    return await serializer.from_queryset(model.all())


async def get_one(serializer, **data):
    model = serializer.__config__.orig_model
    return await serializer.from_queryset_single(model.get(**data))

async def filter_by(serializer, **filters):
    model = serializer.__config__.orig_model
    return await serializer.from_queryset(model.filter(**filters))

async def create(serializer, **data):
    model = serializer.__config__.orig_model
    db_obj = await model.create(**data)
    return await serializer.from_tortoise_orm(db_obj)

async def update(serializer, obj_id, **data):
    model = serializer.__config__.orig_model
    qs = model.filter(id=obj_id)
    await qs.update(**data)
    if hasattr(qs, "update_bw_relations"):
        await qs.update_bw_relations(obj_id)
    return await serializer.from_queryset_single(model.get(id=obj_id))

async def main():
    await Tortoise.init(
        db_url=settings.db_url,
        modules={'models': ['main.api.models']}
    )

    products = {}
    appliances = {}
    brands = {}
    providers = {}
    provider_products = {}

    with open('products-seed.sql', 'r') as sqlfile:
        for line in sqlfile.readlines():
            if line.startswith('INSERT INTO '):
                model_name = line.split('`')[1]
                if model_name == 'database_appliance':
                    for row in line[41:-3].split("),("):
                        _id, name = row.split(",")
                        _id = int(_id)
                        name = name.replace("'", "")
                        # print(_id, name)
                        try:
                            appliances[_id] = (await create(ApplianceSerializer, **{"id":_id, "name":name}))
                        except tortoise.exceptions.IntegrityError:
                            appliances[_id] = (await get_one(ApplianceSerializer, name=name))
                if model_name == 'database_brand':
                    for row in line[37:-3].split("),("):
                        _id, name = row.split(",")
                        _id = int(_id)
                        name = name.replace("'", "")
                        # print(_id, name)
                        try:
                            brands[_id] = (await create(BrandSerializer, **{"id":_id, "name":name}))
                        except tortoise.exceptions.IntegrityError:
                            brands[_id] = (await get_one(BrandSerializer, name=name))
                if model_name == 'database_provider':
                    for row in line[40:-3].split("),("):
                        _id, name = row.split(",")
                        _id = int(_id)
                        name = name.replace("'", "")
                        # print(_id, name)
                        try:
                            providers[_id] = (await create(ProviderSerializer, **{"id":_id, "name":name}))
                        except tortoise.exceptions.IntegrityError:
                            providers[_id] = (await get_one(ProviderSerializer, name=name))
                if model_name == 'database_product':
                    for row in line[39:-3].split("),("):
                        # print(row)
                        try:
                            _id, code, name, description, price, discount, appliance_id, brand_id, provider_id, picture = row.split(",")
                        except ValueError:
                            splitted = row.split(",")
                            _id, code, name = splitted[:3]
                            price, discount, appliance_id, brand_id, provider_id, picture = splitted[-6:]
                            description = ",".join(splitted[3:-6])
                        _id = int(_id)
                        code = code.replace("'", "")
                        name = name.replace("'", "")
                        description = description.replace("'", "")
                        price = float(price)
                        discount = float(discount)
                        appliance_id = int(appliance_id) if appliance_id.isdigit() else None
                        brand_id = int(brand_id)
                        provider_id = int(provider_id)
                        picture = picture.replace("'", "")
                        data = {
                            "id":_id,
                            "code": code,
                            "name":name,
                            "description":description,
                            "brand_id":brands[brand_id].id
                        }
                        if appliance_id:
                            data["appliance_id"] = appliances[appliance_id].id
                        products[_id] = (await create(ProductSerializer, **data))
                        if not providers[provider_id].id in provider_products.keys():
                            provider_products[providers[provider_id].id] = []
                        provider_products[providers[provider_id].id].append({"product_id":products[_id].id, "price":price, "discount":discount})
                # print(model_name)

    for p_id, pp in provider_products.items():
        await update(ProviderSerializer, p_id, **{"provider_products":pp})

    # import pdb; pdb.set_trace()
    await Tortoise.close_connections()

asyncio.run(main())