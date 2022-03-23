from typing import Dict, List, Optional, Union
import datetime

from pydantic import BaseModel, validator, root_validator
from tortoise.contrib.pydantic import PydanticModel
from tortoise.contrib.pydantic.base import _get_fetch_fields
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.queryset import QuerySet, QuerySetSingle

from main.logger import logger
from main.api.models import Appliance, Brand, Customer, Employee, Order, Organization, Percentage, Product, Provider, Storage, StorageBuy, StorageType, TaxPayer, Work_Employee, WorkBuy, Work


class StatusSchema(BaseModel):
    message: str

class GenericIDSchema(PydanticModel):
    id: int

class GenericIDNameSchema(PydanticModel):
    id: int
    name: str

class GenericNameSchema(PydanticModel):
    name: str

class GenericIDCodeSchema(PydanticModel):
    id: int
    code: str

### Provider

class ProviderContactBaseSchema(PydanticModel):
    name: str
    department: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    for_orders: Optional[bool] = False

class ProviderProductSchema(PydanticModel):
    id: int
    code: str
    product: GenericIDSchema
    price: float
    
    # @validator('product', pre=True)
    # def validate_id(cls, v):
    #     return v["id"] if v else None

class ProviderProductCreateSchema(PydanticModel):
    code: str
    product_id: int
    price: float

class ProviderProductUpdateSchema(PydanticModel):
    id: int
    code: Optional[str]
    product_id: Optional[int]
    price: Optional[float]

class ProviderBaseSchema(PydanticModel):
    name: str
    contacts: Optional[List[ProviderContactBaseSchema]]

class ProviderSchema(ProviderBaseSchema):
    id: int
    provider_products: Optional[List[ProviderProductSchema]]
    products_amount: int

    @root_validator(pre=True)
    def root_validator_pre(cls, v):
        v['products_amount'] = len(v['provider_products'])
        return v

class ProviderCreateSchema(ProviderBaseSchema):
    provider_products: Optional[List[ProviderProductCreateSchema]]

class ProviderUpdateSchema(ProviderBaseSchema):
    provider_products: Optional[List[Union[ProviderProductUpdateSchema, ProviderProductCreateSchema]]]

ProviderSerializer = pydantic_model_creator(Provider, exclude=(
    "orders",
    'provider_products.product.brand',
    'provider_products.product.appliance',
    'provider_products.product.provider_products',
    "provider_products.product.work_products",
    "provider_products.product.customer_products",
    "provider_products.order_provider_products",
))
ProviderSerializer.Config.schema = ProviderSchema
ProviderSerializer.Config.create_schema = ProviderCreateSchema
ProviderSerializer.Config.update_schema = ProviderUpdateSchema

### Customer

class CustomerContactBaseSchema(PydanticModel):
    name: str
    department: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    for_quotation: Optional[bool] = False

class CustomerProductSchema(PydanticModel):
    id: int
    code: str
    product: GenericIDSchema
    price: float
    
    # @validator('product', pre=True)
    # def validate_id(cls, v):
    #     return v["id"] if v else None

class CustomerProductCreateSchema(PydanticModel):
    code: str
    product_id: int
    price: float

class CustomerProductUpdateSchema(PydanticModel):
    id: int
    code: Optional[str]
    product_id: Optional[int]
    price: Optional[float]

class CustomerBaseSchema(PydanticModel):
    name: str
    contacts: Optional[List[CustomerContactBaseSchema]]

class CustomerSchema(CustomerBaseSchema):
    id: int
    customer_products: Optional[List[CustomerProductSchema]]
    products_amount: int

    @root_validator(pre=True)
    def root_validator_pre(cls, v):
        v['products_amount'] = len(v['customer_products'])
        return v

class CustomerCreateSchema(CustomerBaseSchema):
    customer_products: Optional[List[CustomerProductCreateSchema]]

class CustomerUpdateSchema(CustomerBaseSchema):
    customer_products: Optional[List[Union[CustomerProductUpdateSchema, CustomerProductCreateSchema]]]

CustomerSerializer = pydantic_model_creator(Customer, exclude=(
    'customer_products.product.brand',
    'customer_products.product.appliance',
    'customer_products.product.provider_products'
    'customer_products.work_customer_products',
    "storages", "works", "workbuys", "storagebuys"))
CustomerSerializer.Config.schema = CustomerSchema
CustomerSerializer.Config.create_schema = CustomerCreateSchema
CustomerSerializer.Config.update_schema = CustomerUpdateSchema


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

ProductSerializer = pydantic_model_creator(Product, exclude=("provider_products", "work_products", "customer_products"))
ProductSerializer.Config.schema = ProductSchema
ProductSerializer.Config.create_schema = ProductCreateSchema
ProductSerializer.Config.update_schema = ProductUpdateSchema


### Percentage

class PercentageSchema(PydanticModel):
    id: int
    max_price_limit: float
    increment: float

class PercentageCreateSchema(PydanticModel):
    max_price_limit: float
    increment: float

class PercentageUpdateSchema(PydanticModel):
    max_price_limit: Optional[float]
    increment: Optional[float]

PercentageSerializer = pydantic_model_creator(Percentage)
PercentageSerializer.Config.schema = PercentageSchema
PercentageSerializer.Config.create_schema = PercentageCreateSchema
PercentageSerializer.Config.update_schema = PercentageUpdateSchema


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
    organization: GenericIDNameSchema
    storagetype: GenericIDNameSchema

class StorageSchema(StorageBaseSchema):
    id: int
    
    # @validator('organization', 'storagetype', pre=True)
    # def validate_id(cls, v):
    #     return v["id"] if v else None

class StorageCreateSchema(PydanticModel):
    organization_id: int
    storagetype_id: int

class StorageUpdateSchema(PydanticModel):
    organization_id: Optional[int]
    storagetype_id: Optional[int]

StorageSerializer = pydantic_model_creator(Storage)
StorageSerializer.Config.schema = StorageSchema
StorageSerializer.Config.create_schema = StorageCreateSchema
StorageSerializer.Config.update_schema = StorageUpdateSchema


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
    id: int
    provider_product: GenericIDCodeSchema
    amount: int
    price: float

class OrderProductCreateSchema(PydanticModel):
    provider_product_id: int
    amount: int
    price: float

class OrderProductUpdateSchema(PydanticModel):
    id: int
    provider_product_id: Optional[int]
    amount: Optional[int]
    price: Optional[float]

class UnregisteredProductSchema(PydanticModel):
    id: int
    code: Optional[str]
    description: str
    amount: int
    price: Optional[float]

class UnregisteredProductCreateSchema(PydanticModel):
    code: Optional[str]
    description: str
    amount: int
    price: Optional[float]

class UnregisteredProductUpdateSchema(PydanticModel):
    id: int
    code: Optional[str]
    description: Optional[str]
    amount: Optional[int]
    price: Optional[float]

class PaymentSchema(PydanticModel):
    id: int
    date: datetime.date
    amount: float
    method: str

class PaymentCreateSchema(PydanticModel):
    date: datetime.date
    amount: float
    method: str

class PaymentUpdateSchema(PydanticModel):
    id: int
    date: Optional[datetime.date]
    amount: Optional[float]
    method: Optional[str]

class OrderBaseSchema(PydanticModel):
    authorized: Optional[bool] = False
    include_iva: Optional[bool] = False
    discount: Optional[float] = 0.0
    comment: Optional[str] = ""
    state: Optional[str]
    has_invoice: Optional[bool] = False
    invoice_number: Optional[str]
    invoice_uuid: Optional[str]
    invoice_date: Optional[datetime.date]
    due: Optional[datetime.date]

class OrderSchema(OrderBaseSchema):
    id: int
    created_at: datetime.datetime
    provider: GenericIDNameSchema
    taxpayer: GenericIDNameSchema
    claimant: Optional[GenericIDNameSchema]
    order_provider_products: Optional[List[OrderProductSchema]]
    order_unregisteredproducts: Optional[List[UnregisteredProductSchema]]
    payments: Optional[List[PaymentSchema]]
    subtotal: float
    total: float
    workbuy_number: Optional[str]
    storagebuy_number: Optional[str]

    @root_validator(pre=True)
    def root_validator_pre(cls, v):
        v['subtotal'] = 0.0
        for op in v['order_provider_products']:
            v['subtotal'] += op['amount'] * float(op['price'])
        for oup in v['order_unregisteredproducts']:
            v['subtotal'] += oup['amount'] * float(oup['price'])
        v['total'] = v['subtotal']
        v['total'] -= float(v['discount'] or 0.0) or 0.0
        if v['include_iva']:
            v['total'] += v['total']*0.16
        if v.get('workbuy'):
            v['workbuy_number'] = v['workbuy']['organization']['prefix'] + str(v['workbuy']['id'])
        if v.get('storagebuy'):
            v['storagebuy_number'] = v['storagebuy']['organization']['prefix'] + str(v['storagebuy']['id'])
        return v

class OrderCreateSchema(OrderBaseSchema):
    provider_id: int
    taxpayer_id: int
    claimant_id: Optional[int]
    order_provider_products: Optional[List[OrderProductCreateSchema]]
    order_unregisteredproducts: Optional[List[UnregisteredProductCreateSchema]]
    payments: Optional[List[PaymentCreateSchema]]

class OrderUpdateBaseSchema(OrderBaseSchema):
    claimant_id: Optional[int]
    taxpayer_id: Optional[int]
    order_provider_products: Optional[List[Union[OrderProductUpdateSchema, OrderProductCreateSchema]]]
    order_unregisteredproducts: Optional[List[Union[UnregisteredProductCreateSchema, UnregisteredProductUpdateSchema]]]
    payments: Optional[List[Union[PaymentUpdateSchema, PaymentCreateSchema]]]

class OrderUpdateSchema(OrderUpdateBaseSchema):
    id: int

OrderSerializer = pydantic_model_creator(Order, exclude=(
    "provider.contacts",
    "provider.provider_products",
    "taxpayer.works",
    "claimant.work_employees",
    'order_provider_products.provider_product.provider',
    'order_provider_products.provider_product.product'
    "workbuy.customer",
    'workbuy.organization.storages',
    'workbuy.organization.storagebuys',
    'workbuy.organization.works',
    "workbuy.works",
    "storagebuy.storage",
    "storagebuy.customer",
    'storagebuy.organization.storages',
    'storagebuy.organization.workbuys',
    'storagebuy.organization.works',
))
OrderSerializer.Config.schema = OrderSchema
OrderSerializer.Config.create_schema = OrderCreateSchema
OrderSerializer.Config.update_schema = OrderUpdateBaseSchema



### WorkSerializer

class WorkEmployeeSchema(PydanticModel):
    id: int
    employee: GenericIDNameSchema

class WorkEmployeeCreateSchema(PydanticModel):
    employee_id: int

class WorkEmployeeUpdateSchema(PydanticModel):
    id: int
    employee_id: Optional[int]

class WorkCustomerProductSchema(PydanticModel):
    id: int
    customer_product: GenericIDCodeSchema
    amount: int
    price: float

class WorkCustomerProductCreateSchema(PydanticModel):
    customer_product_id: int
    amount: int
    price: float

class WorkCustomerProductUpdateSchema(PydanticModel):
    id: int
    customer_product_id: Optional[int]
    amount: Optional[int]
    price: Optional[float]

class WorkProductSchema(PydanticModel):
    id: int
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

class WorkProductUpdateSchema(PydanticModel):
    id: int
    product_id: Optional[int]
    amount: Optional[int]
    price: Optional[float]

class WorkMinimalSchema(PydanticModel):
    id: int
    taxpayer: GenericIDNameSchema
    include_iva: Optional[bool] = False
    discount: Optional[float] = 0.0
    subtotal: float
    total: float
    work_products: Optional[List[WorkProductMinimalSchema]]
    work_customer_products: Optional[List[WorkProductMinimalSchema]]
    work_unregisteredproducts: Optional[List[UnregisteredProductSchema]]

    @root_validator(pre=True)
    def root_validator_pre(cls, v):
        v['subtotal'] = 0.0
        for op in v['work_products']:
            v['subtotal'] += op['amount'] * float(op['price'])
        for op in v['work_customer_products']:
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
    requires_invoice: Optional[bool] = False
    has_credit: Optional[bool] = False
    include_iva: Optional[bool] = False
    discount: Optional[float] = 0.0
    comment: Optional[str]
    invoice_number: Optional[str]
    invoice_uuid: Optional[str]
    invoice_date: Optional[datetime.date]

class WorkSchema(WorkBaseSchema):
    id: int
    created_at: datetime.datetime
    number: str
    taxpayer: GenericIDNameSchema
    work_products: Optional[List[WorkProductSchema]]
    work_customer_products: Optional[List[WorkCustomerProductSchema]]
    work_unregisteredproducts: Optional[List[UnregisteredProductSchema]]
    work_employees: Optional[List[WorkEmployeeSchema]]
    payments: Optional[List[PaymentSchema]]
    has_invoice: Optional[bool] = False
    customer: GenericIDNameSchema
    state: str
    due: Optional[datetime.date]
    subtotal: float
    total: float
    workbuy_id: Optional[int]

    @root_validator(pre=True)
    def root_validator_pre(cls, v):
        v['subtotal'] = 0.0
        for op in v['work_products']:
            v['subtotal'] += op['amount'] * float(op['price'])
        for op in v['work_customer_products']:
            v['subtotal'] += op['amount'] * float(op['price'])
        for oup in v['work_unregisteredproducts']:
            v['subtotal'] += oup['amount'] * float(oup['price'])
        v['total'] = v['subtotal']
        v['total'] -= float(v['discount'] or 0.0) or 0.0
        if v['include_iva']:
            v['total'] += v['total']*0.16
        v['customer'] = v["workbuy"]["customer"]
        v["workbuy_id"] = v["workbuy"].get("id")
        return v

class WorkCreateSchema(WorkBaseSchema):
    number: str
    taxpayer_id: int
    work_products: Optional[List[WorkProductCreateSchema]]
    work_customer_products: Optional[List[WorkCustomerProductCreateSchema]]
    work_unregisteredproducts: Optional[List[UnregisteredProductCreateSchema]]
    work_employees: Optional[List[WorkEmployeeCreateSchema]]
    payments: Optional[List[PaymentCreateSchema]]

class WorkUpdateBaseSchema(WorkBaseSchema):
    number: Optional[str]
    taxpayer_id: Optional[int]
    work_products: Optional[List[Union[WorkProductUpdateSchema, WorkProductCreateSchema]]]
    work_customer_products: Optional[List[Union[WorkCustomerProductUpdateSchema, WorkCustomerProductCreateSchema]]]
    work_unregisteredproducts: Optional[List[Union[UnregisteredProductUpdateSchema, UnregisteredProductCreateSchema]]]
    work_employees: Optional[List[Union[WorkEmployeeUpdateSchema, WorkEmployeeCreateSchema]]]
    payments: Optional[List[Union[PaymentUpdateSchema, PaymentCreateSchema]]]

class WorkUpdateSchema(WorkBaseSchema):
    id: int


WorkSerializer = pydantic_model_creator(Work, exclude=(
    'customer.contacts',
    'customer.storagebuys',
    'customer.workbuys',
    'customer.customer_products',
    'organization.storages',
    'organization.storagebuys',
    'organization.workbuys',
    'taxpayer.orders',
    # 'workbuy.customer',
    'workbuy.organization',
    'workbuy.orders',
    'work_employees.employee.orders',
))
WorkSerializer.Config.schema = WorkSchema
WorkSerializer.Config.create_schema = WorkCreateSchema
WorkSerializer.Config.update_schema = WorkUpdateBaseSchema



### WorkBuy

class WorkBuySchema(PydanticModel):
    id: int
    number: str
    created_at: datetime.datetime
    customer: GenericIDNameSchema
    organization: OrganizationSchema
    orders: Optional[List[OrderSchema]]
    works: Optional[List[WorkSchema]]
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
            w['workbuy'] = v
            w = WorkSchema.root_validator_pre(w)
            v['works_total'] += w['total']
        v['earnings'] = v['works_total'] - v['total']
        return v


class WorkBuyCreateSchema(PydanticModel):
    customer_id: int
    organization_id: int
    orders: Optional[List[OrderCreateSchema]]
    works: Optional[List[WorkCreateSchema]]

class WorkBuyUpdateSchema(PydanticModel):
    customer_id: Optional[int]
    organization_id: Optional[int]
    orders: List[Union[OrderUpdateSchema, OrderCreateSchema]]
    works: List[Union[WorkUpdateSchema, WorkCreateSchema]]

    # @root_validator(pre=True)
    # def root_validator_pre(cls, v):
    #     import pdb; pdb.set_trace()
    #     return v

WorkBuySerializer = pydantic_model_creator(WorkBuy, exclude=(
    'customer.contacts',
    'customer.storagebuys',
    'customer.workbuys',
    'customer.works',
    'customer.customer_products',
    'organization.storages',
    'organization.storagebuys',
    'organization.workbuys',
    'organization.works',
    'orders.provider.contacts',
    'orders.provider.provider_products',
    'orders.taxpayer.works',
    'orders.claimant.work_employees',
    'orders.storagebuy',
    'orders.payments',
    'works.customer',
    'works.organization',
    'works.taxpayer.orders',
    'works.payments',
    'works.work_employees',
    # 'works.work_products.product',
    'works.work_customer_products.product',
))
WorkBuySerializer.Config.schema = WorkBuySchema
WorkBuySerializer.Config.create_schema = WorkBuyCreateSchema
WorkBuySerializer.Config.update_schema = WorkBuyUpdateSchema


### StorageBuy

class StorageBuySchema(PydanticModel):
    id: int
    number: str
    created_at: datetime.datetime
    customer: GenericIDNameSchema
    storage: StorageSchema
    organization: OrganizationSchema
    orders: Optional[List[OrderSchema]]
    orders_number: int
    total: float

    @root_validator(pre=True)
    def root_validator_pre(cls, v):
        v['number'] = v["organization"]['prefix'] + str(v["id"])
        v['orders_number'] = len(v['orders'] or [])
        v['total'] = 0.0
        for o in v['orders']:
            o['storagebuy'] = v
            o = OrderSchema.root_validator_pre(o)
            v['total'] += o['total']
        return v


class StorageBuyCreateSchema(PydanticModel):
    customer_id: int
    organization_id: int
    storage_id: int
    orders: Optional[List[OrderCreateSchema]]

class StorageBuyUpdateSchema(PydanticModel):
    customer_id: Optional[int]
    organization_id: Optional[int]
    storage_id: Optional[int]
    orders: List[Union[OrderCreateSchema, OrderUpdateSchema]]

StorageBuySerializer = pydantic_model_creator(StorageBuy, exclude=(
    'customer.contacts',
    'customer.storagebuys',
    'customer.workbuys',
    'customer.works',
    'customer.customer_products',
    'organization.storages',
    'organization.storagebuys',
    'organization.workbuys',
    'organization.works',
    'orders.provider.contacts',
    'orders.provider.provider_products',
    'orders.taxpayer.works',
    'orders.claimant.work_employees',
    'orders.workbuy',
    'orders.payments',
))
StorageBuySerializer.Config.schema = StorageBuySchema
StorageBuySerializer.Config.create_schema = StorageBuyCreateSchema
StorageBuySerializer.Config.update_schema = StorageBuyUpdateSchema


class WorkOrderSchema(PydanticModel):
    work_product_providers: Optional[Dict[int, int]] = {}
    work_unregisteredproduct_providers: Optional[Dict[int, int]] = {}
    work_customer_product_providers: Optional[Dict[int, int]] = {}

class WorkOrderCreateSchema(OrderCreateSchema):
    workbuy_id: int