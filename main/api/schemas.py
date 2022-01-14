from typing import List, Optional, Union
import datetime

from pydantic import BaseModel, validator, root_validator
from tortoise.contrib.pydantic import PydanticModel
from tortoise.contrib.pydantic.base import _get_fetch_fields
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.queryset import QuerySet, QuerySetSingle

from main.logger import logger
from main.api.models import Appliance, Brand, Customer, Employee, Order, Organization, Product, Provider, Storage, StorageType, TaxPayer, Work_Employee, WorkBuy, Work


class StatusSchema(BaseModel):
    message: str

class GenericIDSchema(PydanticModel):
    id: int

class GenericIDNameSchema(PydanticModel):
    id: int
    name: str

class GenericNameSchema(PydanticModel):
    name: str

### Provider

class ProviderContactBaseSchema(PydanticModel):
    name: str
    department: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    for_orders: Optional[bool] = False

class ProviderProductSchema(PydanticModel):
    id: int
    product: int
    price: float
    discount: Optional[float]
    
    @validator('product', pre=True)
    def validate_id(cls, v):
        return v["id"] if v else None

class ProviderBaseSchema(PydanticModel):
    name: str
    contacts: Optional[List[ProviderContactBaseSchema]]
    provider_products: Optional[List[ProviderProductSchema]]

class ProviderSchema(ProviderBaseSchema):
    id: int

class ProviderUpdateSchema(ProviderBaseSchema):
    name: Optional[str]

ProviderSerializer = pydantic_model_creator(Provider, exclude=("orders","provider_products.order_products","provider_products.product.work_products"))
ProviderSerializer.Config.schema = ProviderSchema
ProviderSerializer.Config.create_schema = ProviderBaseSchema
ProviderSerializer.Config.update_schema = ProviderUpdateSchema

### Customer

class CustomerContactBaseSchema(PydanticModel):
    name: str
    department: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    for_quotation: Optional[bool] = False

class CustomerBaseSchema(PydanticModel):
    name: str
    contacts: Optional[List[CustomerContactBaseSchema]]

class CustomerSchema(CustomerBaseSchema):
    id: int

CustomerSerializer = pydantic_model_creator(Customer, exclude=("storages", "works", "workbuys"))
CustomerSerializer.Config.schema = CustomerSchema
CustomerSerializer.Config.create_schema = CustomerBaseSchema


### Brand

# class BrandBaseSchema(PydanticModel):
#     name: str

# class BrandSchema(BrandBaseSchema):
#     id: int

BrandSerializer = pydantic_model_creator(Brand)
BrandSerializer.Config.schema = GenericIDNameSchema
BrandSerializer.Config.create_schema = GenericNameSchema


### Appliance

# class ApplianceBaseSchema(PydanticModel):
#     name: str

# class ApplianceSchema(ApplianceBaseSchema):
#     id: int
    
ApplianceSerializer = pydantic_model_creator(Appliance)
ApplianceSerializer.Config.schema = GenericIDNameSchema
ApplianceSerializer.Config.create_schema = GenericNameSchema


### Product

class ProductBaseSchema(PydanticModel):
    code: str
    name: str
    description: Optional[str]

class ProductSchema(ProductBaseSchema):
    id: int
    brand: GenericIDNameSchema
    appliance: Optional[GenericIDNameSchema]

class ProductCreateSchema(ProductBaseSchema):
    brand_name: str
    appliance_name: Optional[str]

class ProductUpdateSchema(ProductCreateSchema):
    code: Optional[str]
    name: Optional[str]
    brand_name: Optional[str]

ProductSerializer = pydantic_model_creator(Product, exclude=("provider_products", "work_products"))
ProductSerializer.Config.schema = ProductSchema
ProductSerializer.Config.create_schema = ProductCreateSchema
ProductSerializer.Config.update_schema = ProductUpdateSchema


### Organization

class OrganizationBaseSchema(PydanticModel):
    name: str
    prefix: Optional[str]

class OrganizationSchema(OrganizationBaseSchema):
    id: int
    
OrganizationSerializer = pydantic_model_creator(Organization, exclude=("storages", "storagebuys", "works", "workbuys"))
OrganizationSerializer.Config.schema = OrganizationSchema
OrganizationSerializer.Config.create_schema = OrganizationBaseSchema

### Taxpayer

class TaxPayerBaseSchema(PydanticModel):
    name: str
    key: str

class TaxpayerSchema(TaxPayerBaseSchema):
    id: int
    
TaxPayerSerializer = pydantic_model_creator(TaxPayer, exclude=("orders", "works"))
TaxPayerSerializer.Config.schema = TaxpayerSchema
TaxPayerSerializer.Config.create_schema = TaxPayerBaseSchema


### StorageType

# class StorageTypeBaseSchema(PydanticModel):
#     name: str

# class StorageTypeSchema(StorageTypeBaseSchema):
#     id: int

StorageTypeSerializer = pydantic_model_creator(StorageType)
StorageTypeSerializer.Config.schema = GenericIDNameSchema
StorageTypeSerializer.Config.create_schema = GenericNameSchema


### Storage

class StorageBaseSchema(PydanticModel):
    organization: int
    storagetype: int

class StorageSchema(StorageBaseSchema):
    id: int
    
    @validator('organization', 'storagetype', pre=True)
    def validate_id(cls, v):
        return v["id"] if v else None

StorageSerializer = pydantic_model_creator(Storage)
StorageSerializer.Config.schema = StorageSchema
StorageSerializer.Config.create_schema = StorageBaseSchema


### Employee

class EmployeeBaseSchema(PydanticModel):
    name: str
    phone: Optional[str]

class EmployeeSchema(EmployeeBaseSchema):
    id: int

EmployeeSerializer = pydantic_model_creator(Employee, exclude=("orders", "work_employees"))
EmployeeSerializer.Config.schema = EmployeeSchema
EmployeeSerializer.Config.create_schema = EmployeeBaseSchema


### Order


class OrderProductSchema(PydanticModel):
    provider_product: GenericIDSchema
    amount: int
    price: float

class OrderProductCreateSchema(PydanticModel):
    provider_product_id: int
    amount: int
    price: float

class UnregisteredProductSchema(PydanticModel):
    code: Optional[str]
    description: str
    amount: int
    price: Optional[float]

class OrderBaseSchema(PydanticModel):
    authorized: Optional[bool] = False
    include_iva: Optional[bool] = False
    discount: Optional[float] = 0.0
    comment: Optional[str] = ""
    state: Optional[str]
    # workbuy_id: Optional[int]
    # storagebuy_id: Optional[int]
    has_invoice: Optional[bool] = False
    invoice_number: Optional[str]
    invoice_uuid: Optional[str]
    invoice_date: Optional[datetime.date]
    due: Optional[datetime.date]
    order_products: Optional[List[OrderProductSchema]]
    order_unregisteredproducts: Optional[List[UnregisteredProductSchema]]

class OrderSchema(OrderBaseSchema):
    id: int
    created_at: datetime.datetime
    provider: GenericIDNameSchema
    taxpayer: GenericIDNameSchema
    claimant: Optional[GenericIDNameSchema]
    subtotal: float
    total: float
    workbuy_number: Optional[str]

    @root_validator(pre=True)
    def root_validator_pre(cls, v):
        v['subtotal'] = 0.0
        for op in v['order_products']:
            v['subtotal'] += op['amount'] * float(op['price'])
        for oup in v['order_unregisteredproducts']:
            v['subtotal'] += oup['amount'] * float(oup['price'])
        v['total'] = v['subtotal']
        v['total'] -= float(v['discount'] or 0.0) or 0.0
        if v['include_iva']:
            v['total'] += v['total']*0.16
        if v.get('workbuy'):
            v['workbuy_number'] = v['workbuy']['organization']['prefix'] + str(v['workbuy']['id'])
        return v

class OrderCreateSchema(OrderBaseSchema):
    provider_id: int
    taxpayer_id: int
    claimant_id: Optional[int]
    order_products: Optional[List[OrderProductCreateSchema]]

class OrderUpdateSchema(OrderBaseSchema):
    claimant_id: Optional[int]
    taxpayer_id: Optional[int]
    order_products: Optional[List[OrderProductCreateSchema]]

class OrderIDSchema(PydanticModel):
    id: int

class OrderUpdateSpecialSchema(OrderUpdateSchema):
    id: Optional[int]
    provider_id: int
    taxpayer_id: int
    claimant_id: Optional[int]

OrderSerializer = pydantic_model_creator(Order, exclude=(
    "provider.contacts",
    "provider.provider_products",
    "taxpayer.works",
    "claimant.work_employees",
    "workbuy.customer",
    # "workbuy.organization",
    'workbuy.organization.storages',
    'workbuy.organization.storagebuys',
    'workbuy.organization.works',
    "workbuy.works",
    "storagebuy.storage",
    "storagebuy.customer",
    "storagebuy.organization"
))
OrderSerializer.Config.schema = OrderSchema
OrderSerializer.Config.create_schema = OrderCreateSchema
OrderSerializer.Config.update_schema = OrderUpdateSchema



### WorkSerializer

class WorkEmployeeSchema(PydanticModel):
    id: int
    employee: GenericIDNameSchema

class WorkEmployeeCreateSchema(PydanticModel):
    employee_id: int

class WorkProductSchema(PydanticModel):
    product: GenericIDSchema
    amount: int
    price: float

class WorkProductMinimalSchema(PydanticModel):
    amount: int
    price: float

class WorkProductCreateSchema(PydanticModel):
    product_id: int
    amount: int
    price: float

class WorkMinimalSchema(PydanticModel):
    id: int
    include_iva: Optional[bool] = False
    discount: Optional[float] = 0.0
    subtotal: float
    total: float
    work_products: Optional[List[WorkProductMinimalSchema]]
    work_unregisteredproducts: Optional[List[UnregisteredProductSchema]]

    @root_validator(pre=True)
    def root_validator_pre(cls, v):
        v['subtotal'] = 0.0
        for op in v['work_products']:
            v['subtotal'] += op['amount'] * float(op['price'])
        for oup in v['work_unregisteredproducts']:
            v['subtotal'] += oup['amount'] * float(oup['price'])
        v['total'] = v['subtotal']
        v['total'] -= float(v['discount'] or 0.0) or 0.0
        if v['include_iva']:
            v['total'] += v['total']*0.16
        return v

class WorkBaseSchema(PydanticModel):
    unit: Optional[str]
    model: Optional[str]
    authorized: Optional[bool] = False
    include_iva: Optional[bool] = False
    discount: Optional[float] = 0.0
    comment: Optional[str]
    workbuy_id: Optional[int]
    invoice_number: Optional[str]
    invoice_uuid: Optional[str]
    invoice_date: Optional[datetime.date]
    work_unregisteredproducts: Optional[List[UnregisteredProductSchema]]

class WorkSchema(WorkBaseSchema):
    id: int
    created_at: datetime.datetime
    number: str
    customer: GenericIDNameSchema
    organization: OrganizationSchema
    taxpayer: Optional[GenericIDNameSchema]
    work_products: Optional[List[WorkProductSchema]]
    work_employees: Optional[List[WorkEmployeeSchema]]
    has_invoice: Optional[bool] = False
    state: str
    due: Optional[datetime.date]
    subtotal: float
    total: float

    @root_validator(pre=True)
    def root_validator_pre(cls, v):
        v['subtotal'] = 0.0
        for op in v['work_products']:
            v['subtotal'] += op['amount'] * float(op['price'])
        for oup in v['work_unregisteredproducts']:
            v['subtotal'] += oup['amount'] * float(oup['price'])
        v['total'] = v['subtotal']
        v['total'] -= float(v['discount'] or 0.0) or 0.0
        if v['include_iva']:
            v['total'] += v['total']*0.16
        v['workbuy_id'] = (v['workbuy'] or {"id":None})["id"]
        return v

class WorkCreateSchema(WorkBaseSchema):
    number: str
    customer_id: int
    organization_id: int
    taxpayer_id: Optional[int]
    work_products: Optional[List[WorkProductCreateSchema]]
    work_employees: Optional[List[WorkEmployeeCreateSchema]]

class WorkUpdateSchema(WorkBaseSchema):
    number: Optional[str]
    organization_id: Optional[int]
    taxpayer_id: Optional[int]
    work_products: Optional[List[Union[WorkProductCreateSchema, GenericIDSchema]]]
    work_employees: Optional[List[Union[WorkEmployeeCreateSchema, GenericIDSchema]]]


WorkSerializer = pydantic_model_creator(Work, exclude=(
    'customer.contacts',
    'customer.storagebuys',
    'customer.workbuys',
    'organization.storages',
    'organization.storagebuys',
    'organization.workbuys',
    'taxpayer.orders',
    'workbuy.customer',
    'workbuy.organization',
    'workbuy.orders',
    'work_employees.employee.orders',
))
WorkSerializer.Config.schema = WorkSchema
WorkSerializer.Config.create_schema = WorkCreateSchema
WorkSerializer.Config.update_schema = WorkUpdateSchema



### WorkBuy

class WorkBuySchema(PydanticModel):
    id: int
    number: str
    created_at: datetime.datetime
    customer: GenericIDNameSchema
    organization: OrganizationSchema
    orders: Optional[List[OrderSchema]]
    works: Optional[List[WorkMinimalSchema]]
    orders_number: int
    works_number: int
    works_total: float
    total: float
    earnings: float

    @root_validator(pre=True)
    def root_validator_pre(cls, v):
        v['number'] = v["organization"]['prefix'] + str(v["id"])
        v['orders_number'] = len(v['orders'] or [])
        v['total'] = 0.0
        for o in v['orders']:
            o = OrderSchema.root_validator_pre(o)
            v['total'] += o['total']
        v['works_number'] = len(v['works'] or [])
        v['works_total'] = 0.0
        for w in v['works']:
            w = WorkMinimalSchema.root_validator_pre(w)
            v['works_total'] += w['total']
        v['earnings'] = v['works_total'] - v['total']
        return v


class WorkBuyCreateSchema(PydanticModel):
    customer_id: int
    organization_id: int
    orders: Optional[List[OrderCreateSchema]]

class WorkBuyUpdateSchema(PydanticModel):
    customer_id: Optional[int]
    organization_id: Optional[int]
    orders: List[Union[OrderCreateSchema, OrderIDSchema]]

WorkBuySerializer = pydantic_model_creator(WorkBuy, exclude=(
    'customer.contacts',
    'customer.storagebuys',
    'customer.works',
    'organization.storages',
    'organization.storagebuys',
    'organization.works',
    'orders.provider.contacts',
    'orders.provider.provider_products',
    'orders.taxpayer.works',
    'orders.claimant.work_employees',
    'orders.storagebuy',
    'orders.payments',
    'works.customer',
    'works.organization',
    'works.taxpayer',
    'works.payments',
    'works.work_employees',
    'works.work_products.product',
))
WorkBuySerializer.Config.schema = WorkBuySchema
WorkBuySerializer.Config.create_schema = WorkBuyCreateSchema
WorkBuySerializer.Config.update_schema = WorkBuyUpdateSchema