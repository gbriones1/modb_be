import time
from datetime import date, datetime, timedelta
from typing import List, Optional
import json

from fastapi import APIRouter, Depends
from pydantic.main import BaseModel, ModelMetaclass
from tortoise import models
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.contrib.pydantic.base import _get_fetch_fields
from fastapi_pagination import paginate, Page, Params

from main.api.errors import ObjectNotFound
from main.api.auth.schemas import UserSchema
from main.api.auth.dependencies import requires_login, requires_permission
from main.api.schemas import ApplianceSerializer, BrandSerializer, CustomerSerializer, EmployeeSerializer, OrderSchema, OrderSerializer, OrganizationSerializer, PercentageSerializer, ProductSerializer, ProviderSerializer, StatusSchema, StorageBuySerializer, StorageSerializer, StorageTypeSerializer, TaxPayerSerializer, WorkBuySerializer, WorkOrderCreateSchema, WorkOrderSchema, WorkSerializer
from main.logger import logger


router = APIRouter()


crud_endpoints = [
    {
        "pathname": 'provider',
        "serializer": ProviderSerializer,
    }, {
        "pathname": 'customer',
        "serializer": CustomerSerializer,
    }, {
        "pathname": 'employee',
        "serializer": EmployeeSerializer,
    }, {
        "pathname": 'taxpayer',
        "serializer": TaxPayerSerializer,
    }, {
        "pathname": 'organization',
        "serializer": OrganizationSerializer,
    }, {
        "pathname": 'storagetype',
        "serializer": StorageTypeSerializer,
    }, {
        "pathname": 'storage',
        "serializer": StorageSerializer,
    }, {
        "pathname": 'brand',
        "serializer": BrandSerializer,
    }, {
        "pathname": 'appliance',
        "serializer": ApplianceSerializer,
    }, {
        "pathname": 'product',
        "serializer": ProductSerializer,
    }, {
        "pathname": 'percentage',
        "serializer": PercentageSerializer,
    }, {
        "pathname": 'workbuy',
        "serializer": WorkBuySerializer,
        "filter_type": 'datetime_range'
    }, {
        "pathname": 'storagebuy',
        "serializer": StorageBuySerializer,
        "filter_type": 'datetime_range'
    }, {
        "pathname": 'order',
        "serializer": OrderSerializer,
        "filter_type": 'buy_ids',
    }, {
        "pathname": 'work',
        "serializer": WorkSerializer,
        "filter_type": 'buy_ids'
    }, {
        "pathname": 'work_by_date',
        "serializer": WorkSerializer,
        "filter_type": 'datetime_range'
    }
]


def rename(newname):
    def decorator(f):
        f.__name__ = newname
        return f
    return decorator


def register_list(router: APIRouter, pathname: str, serializer: ModelMetaclass, **kwargs):
    model = serializer.__config__.orig_model
    base_schema = getattr(serializer.Config, "schema", serializer)
    if kwargs.get("filter_type") == 'datetime_range':
        @router.get(f"/{pathname}", response_model=List[base_schema])
        @rename(f"list_{pathname}")
        async def crud_list(from_date: Optional[date] = None, to_date: Optional[date] = None, current_user: UserSchema = Depends(requires_login)):
            logger.debug(f"Listing {pathname}")
            if from_date is None:
                from_date = datetime.combine(datetime.utcnow().date(), datetime.min.time()) - timedelta(days=7) + timedelta(seconds=time.timezone)
            else:
                from_date = datetime.combine(from_date, datetime.min.time()) + timedelta(seconds=time.timezone)
            if to_date is None:
                to_date = datetime.combine(datetime.utcnow().date(), datetime.min.time()) + timedelta(days=1) + timedelta(seconds=time.timezone)
            else:
                to_date = datetime.combine(to_date, datetime.min.time()) + timedelta(days=1) + timedelta(seconds=time.timezone)
            logger.debug(f"Filtering from {from_date} to {to_date}")
            range_filters = {}
            if not kwargs.get("on_field"):
                range_filters = {
                    "created_at__gte": from_date,
                    "created_at__lte": to_date
                }
            else:
                range_filters[kwargs["on_field"]+"__gte"] = from_date
                range_filters[kwargs["on_field"]+"__lte"] = to_date
            start = time.time()
            result = await serializer.from_queryset(model.filter(**range_filters).order_by('-id'))
            end = time.time()
            logger.debug(f"Response time: {end-start}")
            logger.debug(f"amount: {len(result)}")
            return result
        return crud_list
    elif kwargs.get("filter_type") == 'buy_ids':
        @router.get(f"/{pathname}", response_model=List[base_schema])
        @rename(f"list_{pathname}")
        async def crud_list(workbuy_ids: Optional[str] = "", storagebuy_ids: Optional[str] = "", current_user: UserSchema = Depends(requires_login)):
            ids_filters = {}
            if workbuy_ids:
                ids_filters["workbuy_id__in"] = workbuy_ids.split(",")
            if storagebuy_ids:
                ids_filters["storagebuy_id__in"] = storagebuy_ids.split(",")
            result = []
            if ids_filters:
                logger.debug(f"Listing {pathname}")
                start = time.time()
                result = await serializer.from_queryset(model.filter(**ids_filters))
                end = time.time()
                logger.debug(f"Response time: {end-start}")
                logger.debug(f"amount: {len(result)}")
            return result
        return crud_list
    @router.get(f"/{pathname}", response_model=List[base_schema])
    @rename(f"list_{pathname}")
    async def crud_list(filters: Optional[str] = "{}", current_user: UserSchema = Depends(requires_login)):
        logger.debug(f"Listing {pathname}")
        # # result = await serializer.from_queryset(model.all())
        # # import pdb; pdb.set_trace()
        # qs = model.all()
        # # pymodel = pydantic_model_creator(model)
        # # result2 = await pymodel.from_queryset(qs)
        # result = await serializer.from_queryset(qs)
        # return result
        # custom_filters = {}
        custom_filters = json.loads(filters)
        start = time.time()
        result = await serializer.from_queryset(model.filter(**custom_filters))
        end = time.time()
        logger.debug(f"Response time: {end-start}")
        return result
    return crud_list


def register_create(router: APIRouter, pathname: str, serializer: ModelMetaclass):
    model = serializer.__config__.orig_model
    base_schema = getattr(serializer.Config, "schema", serializer)
    create_schema = getattr(serializer.Config, "create_schema", base_schema)
    @router.post(f"/{pathname}", response_model=base_schema)
    @rename(f"create_{pathname}")
    async def crud_create(obj: create_schema, u: UserSchema = Depends(requires_permission)):
        data = obj.dict(exclude_unset=True)
        if hasattr(model, "preprocess_create_data"):
            data = await model.preprocess_create_data(**data)
        logger.debug(f"Creating {pathname} with {data}")
        db_obj = await model.create(**data)
        return await serializer.from_tortoise_orm(db_obj)
    return crud_create


def register_get(router: APIRouter, pathname: str, serializer: ModelMetaclass):
    model = serializer.__config__.orig_model
    base_schema = getattr(serializer.Config, "schema", serializer)
    @router.get(f"/{pathname}"+"/{obj_id}", response_model=base_schema, responses={404: {"model": HTTPNotFoundError}})
    @rename(f"get_{pathname}")
    async def crud_get(obj_id: int, u: UserSchema = Depends(requires_login)):
        logger.debug(f"Getting {pathname} {obj_id}")
        return await serializer.from_queryset_single(model.get(id=obj_id))
    return crud_get


def register_update(router: APIRouter, pathname: str, serializer: ModelMetaclass):
    model = serializer.__config__.orig_model
    base_schema = getattr(serializer.Config, "schema", serializer)
    update_schema = getattr(serializer.Config, "update_schema", getattr(serializer.Config, "create_schema", base_schema))
    @router.put(f"/{pathname}"+"/{obj_id}", response_model=base_schema, responses={404: {"model": HTTPNotFoundError}})
    @rename(f"update_{pathname}")
    async def crud_update(obj_id: int, obj: update_schema, u: UserSchema = Depends(requires_permission)):
        logger.debug(f"Data received: {obj.dict()}")
        data = obj.dict(exclude_unset=True)
        if hasattr(model, "preprocess_update_data"):
            data = await model.preprocess_update_data(**data)
        logger.debug(f"Updating {pathname} {obj_id} with {data}")
        qs = model.filter(id=obj_id)
        updated_count = await qs.update(**data)
        if hasattr(qs, "update_bw_relations"):
            await qs.update_bw_relations(obj_id)
        #TODO: Validate update for only bw_relations
        # if not updated_count:
        #     raise ObjectNotFound(model.__name__, {"id":obj_id})
        return await serializer.from_queryset_single(model.get(id=obj_id))
    return crud_update


def register_delete(router: APIRouter, pathname: str, serializer: ModelMetaclass):
    model = serializer.__config__.orig_model
    @rename(f"delete_{pathname}")
    @router.delete(f"/{pathname}"+"/{obj_id}", response_model=StatusSchema, responses={404: {"model": HTTPNotFoundError}})
    async def crud_delete(obj_id: int, u: UserSchema = Depends(requires_permission)):
        logger.debug(f"Deleting {pathname} {obj_id}")
        deleted_count = await model.filter(id=obj_id).delete()
        if not deleted_count:
            raise ObjectNotFound(model.__name__, {"id":obj_id})
        return StatusSchema(message=f"Deleted {pathname} {obj_id}")
    return crud_delete


for endpoint in crud_endpoints:
    # register_list(router, endpoint["pathname"], endpoint["serializer"], endpoint.get("datetime_ranged", False), endpoint.get("datetime_ranged_field"))
    register_list(router, **endpoint)
    register_create(router, endpoint["pathname"], endpoint["serializer"])
    register_get(router, endpoint["pathname"], endpoint["serializer"])
    register_update(router, endpoint["pathname"], endpoint["serializer"])
    register_delete(router, endpoint["pathname"], endpoint["serializer"])


@rename("create_work-order")
@router.post("/work_order/{obj_id}", response_model=List[OrderSchema], responses={404: {"model": HTTPNotFoundError}})
async def create_work_order(obj_id: int, wo:WorkOrderSchema, u: UserSchema = Depends(requires_permission)):
    logger.debug(f"Creating Orders from Work {obj_id}")
    work_data = await WorkSerializer.from_queryset_single(WorkSerializer.__config__.orig_model.get(id=obj_id))
    providers_data = await ProviderSerializer.from_queryset(ProviderSerializer.__config__.orig_model.all())
    ppp_dict = {}
    for p in providers_data:
        ppp_dict[p.id] = {
            'provider': p,
            'provider_products_dict': {}
        }
        for pp in p.provider_products:
            ppp_dict[p.id]['provider_products_dict'][pp.product.id] = pp
    wp_dict = {wp.id:wp for wp in work_data.work_products}
    wup_dict = {wup.id:wup for wup in work_data.work_unregisteredproducts}
    wcp_dict = {wcp.id:wcp for wcp in work_data.work_customer_products}
    orders = {}
    # import pdb; pdb.set_trace()
    for wp_id, p_id in wo.work_product_providers.items():
        wp = wp_dict.get(wp_id)
        ppp = ppp_dict.get(p_id)
        if wp and ppp:
            if ppp["provider"].id not in orders:
                orders[ppp["provider"].id] = {
                    "provider_id": ppp["provider"].id,
                    "taxpayer_id": work_data.taxpayer.id,
                    "workbuy_id": work_data.workbuy.id,
                    "authorized": True,
                    "order_provider_products": [],
                    "order_unregisteredproducts": []
                }
            if wp.product.id in ppp["provider_products_dict"].keys():
                orders[ppp["provider"].id]["order_provider_products"].append({
                    "provider_product_id": ppp["provider_products_dict"][wp.product.id].id,
                    "amount": wp.amount,
                    "price": ppp["provider_products_dict"][wp.product.id].price
                })
            else:
                orders[ppp["provider"].id]["order_unregisteredproducts"].append({
                    "code": wp.product.code,
                    "description": f"{wp.product.name} - {wp.product.description}",
                    "amount": wp.amount,
                    "price": 0
                })
    for wup_id, p_id in wo.work_unregisteredproduct_providers.items():
        wup = wup_dict.get(wup_id)
        ppp = ppp_dict.get(p_id)
        if wup and ppp:
            if ppp["provider"].id not in orders:
                orders[ppp["provider"].id] = {
                    "provider_id": ppp["provider"].id,
                    "taxpayer_id": work_data.taxpayer.id,
                    "workbuy_id": work_data.workbuy.id,
                    "authorized": True,
                    "order_provider_products": [],
                    "order_unregisteredproducts": []
                }
            orders[ppp["provider"].id]["order_unregisteredproducts"].append({
                "code": wup.code,
                "description": wup.description,
                "amount": wup.amount,
                "price": 0
            })
    for wcp_id, p_id in wo.work_customer_product_providers.items():
        wcp = wcp_dict.get(wcp_id)
        ppp = ppp_dict.get(p_id)
        if wcp and ppp:
            if ppp["provider"].id not in orders:
                orders[ppp["provider"].id] = {
                    "provider_id": ppp["provider"].id,
                    "taxpayer_id": work_data.taxpayer.id,
                    "workbuy_id": work_data.workbuy.id,
                    "authorized": True,
                    "order_provider_products": [],
                    "order_unregisteredproducts": []
                }
            if wcp.customer_product.product.id in ppp["provider_products_dict"].keys():
                orders[ppp["provider"].id]["order_provider_products"].append({
                    "provider_product_id": ppp["provider_products_dict"][wcp.customer_product.product.id].id,
                    "amount": wcp.amount,
                    "price": ppp["provider_products_dict"][wcp.customer_product.product.id].price
                })
            else:
                orders[ppp["provider"].id]["order_unregisteredproducts"].append({
                    "code": wcp.customer_product.product.code,
                    "description": f"{wcp.customer_product.product.name} - {wcp.customer_product.product.description}",
                    "amount": wcp.amount,
                    "price": 0
                })
    resp = []
    for order in orders.values():
        if order["order_provider_products"] or order["order_unregisteredproducts"]:
            logger.debug(f"Creating order: {order}")
            # data = WorkOrderCreateSchema(**order)
            db_obj = await OrderSerializer.__config__.orig_model.create(**order)
            resp.append(await OrderSerializer.from_tortoise_orm(db_obj))
        else:
            logger.debug(f"Not creating empty order: {order}")
    return resp