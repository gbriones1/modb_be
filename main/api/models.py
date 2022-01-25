from enum import Enum, unique
from copy import copy
from typing import Any, Dict, List, Type

from tortoise import Tortoise, fields, models
from tortoise.manager import Manager
from tortoise.queryset import QuerySet, UpdateQuery
from tortoise.query_utils import Q

from main.logger import logger

class APIQuerySet(QuerySet):
    
    def _clone(self) -> "APIQuerySet[models.Model]":
        queryset = APIQuerySet.__new__(APIQuerySet)
        queryset.fields = self.fields
        queryset.model = self.model
        queryset.query = self.query
        queryset.capabilities = self.capabilities
        queryset._prefetch_map = copy(self._prefetch_map)
        queryset._prefetch_queries = copy(self._prefetch_queries)
        queryset._single = self._single
        queryset._raise_does_not_exist = self._raise_does_not_exist
        queryset._db = self._db
        queryset._limit = self._limit
        queryset._offset = self._offset
        queryset._fields_for_select = self._fields_for_select
        queryset._filter_kwargs = copy(self._filter_kwargs)
        queryset._orderings = copy(self._orderings)
        queryset._joined_tables = copy(self._joined_tables)
        queryset._q_objects = copy(self._q_objects)
        queryset._distinct = self._distinct
        queryset._annotations = copy(self._annotations)
        queryset._having = copy(self._having)
        queryset._custom_filters = copy(self._custom_filters)
        queryset._group_bys = copy(self._group_bys)
        queryset._select_for_update = self._select_for_update
        queryset._select_for_update_nowait = self._select_for_update_nowait
        queryset._select_for_update_skip_locked = self._select_for_update_skip_locked
        queryset._select_for_update_of = self._select_for_update_of
        queryset._select_related = self._select_related
        queryset._select_related_idx = self._select_related_idx
        queryset._force_indexes = self._force_indexes
        queryset._use_indexes = self._use_indexes
        return queryset

    # def resolve_filters(
    #         self,
    #         model: "models.Model",
    #         q_objects: List[Q],
    #         annotations: Dict[str, Any],
    #         custom_filters: Dict[str, Dict[str, Any]],
    #     ) -> None:
    #     # import pdb; pdb.set_trace()
    #     super().resolve_filters(model, q_objects, annotations, custom_filters)

    def update(self, **kwargs: Any) -> UpdateQuery:
        # import pdb; pdb.set_trace()
        self.bw_relations = {}
        for bw_fk_field in self.model._meta.backward_fk_fields.intersection(set(kwargs.keys())):
            logger.debug(f"BW relation detected for field: {bw_fk_field}")
            self.bw_relations[bw_fk_field] = kwargs.pop(bw_fk_field)
        zero_ids = []
        for field, value in kwargs.items():
            if field.endswith("_id") and value == 0:
                zero_ids.append(field)
        for field in zero_ids:
            kwargs.pop(field)
        uq = super().update(**kwargs)
        return uq

    async def update_bw_relations(self: "APIQuerySet", obj_id: int) -> None:
        if hasattr(self, "bw_relations"):
            await APIQuerySet.update_bw_relations_recursive(self.bw_relations, self.model, obj_id)
    
    @staticmethod
    async def update_bw_relations_recursive(bw_relations: dict, model: models.Model, obj_id: int):
        for field, data_list in bw_relations.items():
            # import pdb; pdb.set_trace()
            logger.debug(f"Updating BW relations for {model.__name__} {obj_id} with data {data_list}")
            new_relations = []
            relation_field = model._meta.fields_map[field].relation_field
            related_model = model._meta.fields_map[field].related_model
            for data in data_list:
                related_bw_relations = {}
                for bw_fk_field in related_model._meta.backward_fk_fields.intersection(set(data.keys())):
                    logger.debug(f"BW relation detected for field: {bw_fk_field}")
                    related_bw_relations[bw_fk_field] = data.pop(bw_fk_field)
                if "id" in data:
                    result = await related_model.get(pk=data["id"])
                    for key, value in data.items():
                        if key != "id":
                            setattr(result, key, value)
                    await result.save()
                else:
                    data[relation_field] = obj_id
                    # result, _ = await related_model.get_or_create(**data)
                    result = related_model(**data)
                    await result.save()
                new_relations.append(result.id)
                if (related_bw_relations):
                    await APIQuerySet.update_bw_relations_recursive(related_bw_relations, related_model, result.id)
            current_related = await related_model.filter(**{relation_field: obj_id})
            for current in current_related:
                if not current.id in new_relations:
                    await current.delete()



class APIManager(Manager):

    def get_queryset(self) -> APIQuerySet:
        return APIQuerySet(self._model)
        

class APIModel(models.Model):

    @classmethod
    async def create(cls: Type[models.Model], **kwargs: Any) -> models.Model:
        logger.debug(f"Creating object with data: {kwargs}")
        bw_relations = {}
        for bw_fk_field in cls._meta.backward_fk_fields.intersection(set(kwargs.keys())):
            logger.debug(f"BW relation detected for field: {bw_fk_field}")
            bw_relations[bw_fk_field] = kwargs.pop(bw_fk_field)
        zero_ids = []
        for field, value in kwargs.items():
            if field.endswith("_id") and value == 0:
                zero_ids.append(field)
        for field in zero_ids:
            kwargs.pop(field)
        # logger.debug(f"Creating object with data: {kwargs}")
        instance = await super().create(**kwargs)
        logger.debug(f"{cls.__name__} ID generated: {instance.id}")
        for field, data_list in bw_relations.items():
            for data in data_list:
                data[cls._meta.fields_map[field].relation_field] = instance.id
                logger.debug(f"Creating BW relation {field} with data: {data}")
                obj = await cls._meta.fields_map[field].related_model.create(**data)
        return instance
    
    @classmethod
    async def preprocess_create_data(cls: Type[models.Model], **kwargs: Any) -> dict:
        return await cls.preprocess_data(**kwargs)

    @classmethod
    async def preprocess_update_data(cls: Type[models.Model], **kwargs: Any) -> dict:
        return await cls.preprocess_data(**kwargs)

    @classmethod
    async def preprocess_data(cls: Type[models.Model], **kwargs: Any) -> dict:
        for fk_field in cls._meta.fk_fields.intersection(set(kwargs.keys())):
            value = kwargs.pop(fk_field)
            if isinstance(value, int):
                kwargs[f"{fk_field}_id"] = value
        for bw_fk_field in cls._meta.backward_fk_fields.intersection(set(kwargs.keys())):
            values = kwargs.pop(bw_fk_field)
            processed_value = []
            for value in values:
                processed_value.append(await cls._meta.fields_map[bw_fk_field].related_model.preprocess_data(**value))
            kwargs[bw_fk_field] = processed_value
        return kwargs


class Appliance(APIModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    
    class Meta:
        manager = APIManager()
        ordering = ["name"]


class Brand(APIModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    
    class Meta:
        manager = APIManager()
        ordering = ["name"]


class TaxPayer(APIModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    key = fields.CharField(max_length=13, unique=True)
    
    class Meta:
        manager = APIManager()
        ordering = ["name"]


class Organization(APIModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    prefix = fields.CharField(max_length=3, unique=True, null=True)

    class Meta:
        manager = APIManager()
        ordering = ["name"]


class StorageType(APIModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)


class Storage(APIModel):
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='storages')
    storagetype = fields.ForeignKeyField('models.StorageType', related_name='storages')

    class Meta:
        unique_together=(("organization", "storagetype"),)


class Employee(APIModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    phone = fields.CharField(max_length=15, unique=True, null=True)

    class Meta:
        manager = APIManager()
        ordering = ["name"]


class Provider(APIModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)

    class Meta:
        manager = APIManager()
        ordering = ["name"]


class ProviderContact(APIModel):
    id = fields.IntField(pk=True)
    provider = fields.ForeignKeyField('models.Provider', related_name='contacts')
    name = fields.CharField(max_length=100)
    department = fields.CharField(max_length=100, null=True, default="")
    email = fields.CharField(max_length=100, null=True, default="")
    phone = fields.CharField(max_length=15, null=True, default="")
    for_orders = fields.BooleanField(default=False)


class Customer(APIModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)

    class Meta:
        manager = APIManager()
        ordering = ["name"]


class CustomerContact(APIModel):
    id = fields.IntField(pk=True)
    customer = fields.ForeignKeyField('models.Customer', related_name='contacts')
    name = fields.CharField(max_length=100)
    department = fields.CharField(max_length=100, null=True, default="")
    email = fields.CharField(max_length=100, null=True, default="")
    phone = fields.CharField(max_length=15, null=True, default="")
    for_quotation = fields.BooleanField(default=False)


class Product(APIModel):
    id = fields.IntField(pk=True)
    code = fields.CharField(max_length=30, unique=True)
    brand = fields.ForeignKeyField('models.Brand', related_name='products', null=True)
    name = fields.CharField(max_length=200)
    description = fields.CharField(max_length=255, null=True)
    appliance = fields.ForeignKeyField('models.Appliance', related_name='products', null=True)
    # picture = fields.ImageField(upload_to='products/', null=True)

    @classmethod
    async def preprocess_create_data(cls: Type[models.Model], **kwargs: Any) -> dict:
        return await cls.preprocess_data(**kwargs)

    @classmethod
    async def preprocess_update_data(cls: Type[models.Model], **kwargs: Any) -> dict:
        return await cls.preprocess_data(**kwargs)

    @classmethod
    async def preprocess_data(cls: Type[models.Model], **kwargs: Any) -> dict:
        brand = kwargs.pop('brand', None)
        if brand:
            kwargs["brand"] = (await Brand.get_or_create(name=brand))[0]
        appliance = kwargs.pop('appliance', None)
        if appliance:
            kwargs["appliance"] = (await Appliance.get_or_create(name=appliance))[0]
        return kwargs


class Provider_Product(APIModel):
    id = fields.IntField(pk=True)
    code = fields.CharField(max_length=30)
    provider = fields.ForeignKeyField('models.Provider', related_name='provider_products', null=True)
    product = fields.ForeignKeyField('models.Product', related_name='provider_products', null=True)
    price = fields.DecimalField(max_digits=9, decimal_places=2)
    
    class Meta:
        unique_together=(("provider", "code"),)

class Customer_Product(APIModel):
    id = fields.IntField(pk=True)
    code = fields.CharField(max_length=30)
    customer = fields.ForeignKeyField('models.Customer', related_name='customer_products', null=True)
    product = fields.ForeignKeyField('models.Product', related_name='customer_products', null=True)
    price = fields.DecimalField(max_digits=9, decimal_places=2)
    
    class Meta:
        unique_together=(("customer", "code"),)

class Percentage(APIModel):
    id = fields.IntField(pk=True)
    max_price_limit = fields.DecimalField(max_digits=9, decimal_places=2, unique=True)
    increment = fields.FloatField()

class WorkBuy(APIModel):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)
    customer = fields.ForeignKeyField('models.Customer', related_name='workbuys')
    organization = fields.ForeignKeyField('models.Organization', related_name='workbuys')

    class Meta:
        manager = APIManager()


class StorageBuy(APIModel):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)
    storage = fields.ForeignKeyField('models.Storage', related_name='storagebuys')
    customer = fields.ForeignKeyField('models.Customer', related_name='storagebuys', null=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='storagebuys')

    class Meta:
        manager = APIManager()


class PaymentMethod(str, Enum):
    cash = 'c'
    transfer = 't'
    check = 'k'
    card = 'd'
    credit = 'r'
    warrant = 'w'


class OrderPayment(APIModel):
    id = fields.IntField(pk=True)
    date = fields.DateField(auto_now_add=True)
    amount = fields.DecimalField(max_digits=9, decimal_places=2)
    order = fields.ForeignKeyField('models.Order', related_name='payments')
    method = fields.CharEnumField(PaymentMethod, max_length=1, default=PaymentMethod.cash)


class Order_Provider_Product(APIModel):
    id = fields.IntField(pk=True)
    order = fields.ForeignKeyField('models.Order', related_name='order_provider_products')
    provider_product = fields.ForeignKeyField('models.Provider_Product', related_name='order_provider_products')
    amount = fields.IntField()
    price = fields.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        manager = APIManager()


class Order_UnregisteredProduct(APIModel):
    id = fields.IntField(pk=True)
    order = fields.ForeignKeyField('models.Order', related_name='order_unregisteredproducts')
    code = fields.CharField(max_length=30, null=True)
    description = fields.CharField(max_length=255)
    amount = fields.IntField()
    price = fields.DecimalField(max_digits=9, decimal_places=2, null=True)

    class Meta:
        manager = APIManager()


class OrderStates(str, Enum):
    cancelled = 'X'
    created = 'A'
    requested = 'B'
    recieved = 'C'


class Order(APIModel):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)
    provider = fields.ForeignKeyField('models.Provider', related_name='orders')
    taxpayer = fields.ForeignKeyField('models.TaxPayer', related_name='orders')
    claimant = fields.ForeignKeyField('models.Employee', related_name='orders', null=True)
    authorized = fields.BooleanField(default=False)
    include_iva = fields.BooleanField(default=False)
    discount = fields.DecimalField(max_digits=9, decimal_places=2, null=True)
    state = fields.CharEnumField(OrderStates, max_length=1, default=OrderStates.created)
    comment = fields.TextField(null=True)
    workbuy = fields.ForeignKeyField('models.WorkBuy', related_name='orders', null=True)
    storagebuy = fields.ForeignKeyField('models.StorageBuy', related_name='orders', null=True)
    has_invoice = fields.BooleanField(default=False)
    invoice_number = fields.CharField(max_length=30, null=True)
    invoice_uuid = fields.UUIDField(null=True)
    invoice_date = fields.DateField(null=True)
    due = fields.DateField(null=True)

    class Meta:
        manager = APIManager()


class WorkStates(str, Enum):
    quoted = 'Q'
    requested = 'R'
    in_progress = 'P'
    cancelled = 'X'
    finished = 'F'
    warrant = 'W'


class Work(APIModel):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)
    number = fields.CharField(max_length=12)
    taxpayer = fields.ForeignKeyField('models.TaxPayer', related_name='works')
    unit = fields.CharField(max_length=30, null=True)
    model = fields.CharField(max_length=30, null=True)
    authorized = fields.BooleanField(default=False)
    include_iva = fields.BooleanField(default=False)
    discount = fields.DecimalField(max_digits=9, decimal_places=2, null=True)
    state = fields.CharEnumField(WorkStates, max_length=1, default=WorkStates.quoted)
    comment = fields.TextField(null=True)
    workbuy = fields.ForeignKeyField('models.WorkBuy', related_name='works')
    has_invoice = fields.BooleanField(default=False)
    invoice_number = fields.CharField(max_length=30, null=True)
    invoice_uuid = fields.UUIDField(null=True)
    invoice_date = fields.DateField(null=True)
    due = fields.DateField(null=True)

    class Meta:
        manager = APIManager()


class WorkPayment(APIModel):
    id = fields.IntField(pk=True)
    date = fields.DateField(auto_now_add=True)
    amount = fields.DecimalField(max_digits=9, decimal_places=2)
    work = fields.ForeignKeyField('models.Work', related_name='payments')
    method = fields.CharEnumField(PaymentMethod, max_length=1, default=PaymentMethod.cash)


class Work_Customer_Product(APIModel):
    id = fields.IntField(pk=True)
    work = fields.ForeignKeyField('models.Work', related_name='work_customer_products')
    customer_product = fields.ForeignKeyField('models.Customer_Product', related_name='work_customer_products')
    amount = fields.IntField()
    price = fields.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        manager = APIManager()


class Work_Product(APIModel):
    id = fields.IntField(pk=True)
    work = fields.ForeignKeyField('models.Work', related_name='work_products')
    product = fields.ForeignKeyField('models.Product', related_name='work_products')
    amount = fields.IntField()
    price = fields.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        manager = APIManager()


class Work_UnregisteredProduct(APIModel):
    id = fields.IntField(pk=True)
    work = fields.ForeignKeyField('models.Work', related_name='work_unregisteredproducts')
    code = fields.CharField(max_length=30, null=True)
    description = fields.CharField(max_length=255)
    amount = fields.IntField()
    price = fields.DecimalField(max_digits=9, decimal_places=2, null=True)

    class Meta:
        manager = APIManager()


class Work_Employee(APIModel):
    id = fields.IntField(pk=True)
    work = fields.ForeignKeyField('models.Work', related_name='work_employees')
    employee = fields.ForeignKeyField('models.Employee', related_name='work_employees')

    class Meta:
        manager = APIManager()
    

Tortoise.init_models(["main.api.models"], "models")