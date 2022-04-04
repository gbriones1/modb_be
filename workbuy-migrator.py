import asyncio
import csv
from datetime import datetime

from tortoise import Tortoise

from main.api.schemas import CustomerSerializer, EmployeeSerializer, OrganizationSerializer, ProductSerializer, ProviderSerializer, TaxPayerSerializer, WorkBuySerializer
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

async def filter_by(serializer, **filters):
    model = serializer.__config__.orig_model
    db_obj = model.filter(**filters)
    # try:
    #     return await serializer.from_queryset(db_obj)
    # except Exception as e:
    #     import pdb; pdb.set_trace()
    #     raise e
    return await serializer.from_queryset(db_obj)

async def create(serializer, **data):
    model = serializer.__config__.orig_model
    try:
        db_obj = await model.create(**data)
    except Exception as e:
        import pdb; pdb.set_trace()
        raise e
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

    # all_providers = await get_all(ProviderSerializer)
    # all_employees = await get_all(EmployeeSerializer)
    # all_organizations = await get_all(OrganizationSerializer)
    # all_taxpayers = await get_all(TaxPayerSerializer)

    workbuys = {}
    ups_count = {}
    ups = {}

    # providers = set()
    # taxpayers = set()
    # customers = set()
    # organizations = set()
    # employees = set()
    # invoices = set()

    failures = 0

    with open('workbuys.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)
        for row in reader:
            w = dict(zip(headers, row))
            if w.get('now') and isfloat(w.get('HOJA', "")) and w.get('ORG') and w.get('OC') and w['ORG'] != 'X' and w['now'] != '   ':
                w_id = int(w['HOJA'])
                if isfloat(w['now']):
                    w_date = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(float(w['now'])) - 2)
                elif w['now']:
                    w_date = datetime.strptime(w['now'], '%d/%m/%Y  %H:%M:%S')
                provider = None
                cust_id = None
                org_id = None
                prov_id = None
                tp_id = None
                empl_id = None
                invoice_number = None
                comment = w.get('OBSERVACION')
                discount = 0.0
                w_price = 0.0
                order_unregisteredproducts = []
                order_provider_products = []
                customer_query = await filter_by(CustomerSerializer, name=w['EMPRESA'] if w['EMPRESA'] else 'DESCONOCIDO')
                if customer_query:
                    cust_id = customer_query[0].id
                elif not dry_run:
                    cust_id = (await create(CustomerSerializer, name=w['EMPRESA'] if w['EMPRESA'] else 'DESCONOCIDO')).id
                organization_query = await filter_by(OrganizationSerializer, prefix=w["OC"][0])
                if organization_query:
                    org_id = organization_query[0].id
                else:
                    organization_query = await filter_by(OrganizationSerializer, name=w["ORG"])
                    if organization_query:
                        org_id = organization_query[0].id
                if not organization_query and not dry_run:
                    org_id = (await create(OrganizationSerializer, name=w['ORG'], prefix=w["OC"][0])).id
                provider_query = await filter_by(ProviderSerializer, name=w['Proveedor'] if w['Proveedor'] else 'DESCONOCIDO')
                if provider_query:
                    provider = provider_query[0]
                    prov_id = provider.id
                elif not dry_run:
                    provider = await create(ProviderSerializer, name=w['Proveedor'] if w['Proveedor'] else 'DESCONOCIDO')
                    prov_id = provider.id
                taxpayer_query = await filter_by(TaxPayerSerializer, name=w['RAZON SOCIAL'] if w['RAZON SOCIAL'] else 'MUELLES OBRERO')
                if taxpayer_query:
                    tp_id = taxpayer_query[0].id
                elif not dry_run:
                    tp_id = (await create(TaxPayerSerializer, name=w['RAZON SOCIAL'] if w['RAZON SOCIAL'] else 'MUELLES OBRERO', key=w['RAZON SOCIAL'][:4]+"010195XYZ" if w['RAZON SOCIAL'] else 'ABCD010195XYZ')).id
                employee_query = await filter_by(EmployeeSerializer, name=w['COMPRA'])
                if employee_query:
                    empl_id = employee_query[0].id
                elif not dry_run:
                    empl_id = (await create(EmployeeSerializer, name=w['COMPRA'])).id
                for i in range(24):
                    if isfloat(w.get(str(i+1)+'_CANT', "")) and isfloat(w.get(str(i+1)+'_IMPORTE', "")) and int(float(w.get(str(i+1)+'_CANT'))) > 0:
                        w_price += (float(w[str(i+1)+'_IMPORTE'])*int(float(w[str(i+1)+'_CANT'])))
                        if len(w[str(i+1)+'_COD']) > 30:
                            w[str(i+1)+'_COD'] = w[str(i+1)+'_COD'][:30]
                        product_query = await filter_by(ProductSerializer, code=w[str(i+1)+'_COD'])
                        if product_query:
                            pp_id = None
                            provider_query = await filter_by(ProviderSerializer, name=w['Proveedor'])
                            if provider_query:
                                provider = provider_query[0]
                                # import pdb; pdb.set_trace()
                                for pp in provider.provider_products:
                                    if pp.product.id == product_query[0].id:
                                        pp_id = pp.id
                                        break
                            if not pp_id and not dry_run:
                                new_pp = []
                                for pp in provider.provider_products:
                                    new_pp.append({'id': pp.id})
                                new_pp.append({"product_id":product_query[0].id, "price":float(w[str(i+1)+'_IMPORTE']), "code":product_query[0].code})
                                await update(ProviderSerializer, provider.id, **{"provider_products":new_pp})
                                provider_query = await filter_by(ProviderSerializer, name=w['Proveedor'])
                                for pp in provider_query[0].provider_products:
                                    if pp.product.id == product_query[0].id:
                                        pp_id = pp.id
                                        break
                            if not dry_run and provider and not pp_id:
                                import pdb; pdb.set_trace()
                            order_provider_products.append({
                                'provider_product_id': pp_id,
                                'amount': int(float(w[str(i+1)+'_CANT'])),
                                'price': float(w[str(i+1)+'_IMPORTE']),
                            })
                        else:
                            if float(w[str(i+1)+'_IMPORTE']) < 0.0:
                                discount = float(w[str(i+1)+'_IMPORTE']) * -1
                            else:
                                if w[str(i+1)+'_COD'] and w[str(i+1)+'_COD'] != "0":
                                    if w[str(i+1)+'_COD'] not in ups_count:
                                        ups_count[w[str(i+1)+'_COD']] = 0
                                        ups[w[str(i+1)+'_COD']] = set()
                                    ups_count[w[str(i+1)+'_COD']] += 1
                                    ups[w[str(i+1)+'_COD']].add(w[str(i+1)+'_REFA'])
                                order_unregisteredproducts.append({
                                    'code': w[str(i+1)+'_COD'],
                                    'description': w[str(i+1)+'_REFA'],
                                    'amount': int(float(w[str(i+1)+'_CANT'])),
                                    'price': float(w[str(i+1)+'_IMPORTE']),
                                })
                w_price = float("{:.2f}".format(w_price))
                if isfloat(w.get('IVA')):
                    iva = float("{:.2f}".format(float(w.get('IVA'))))
                w_iva = True if iva else False
                # impo = 0.0
                # if isfloat(w.get('IMPORETE')):
                #     impo = float("{:.2f}".format(float(w.get('IMPORETE'))))
                # if not w_price == impo:
                #     print(w_id)
                #     print(w_price == impo, w.get('IMPORETE'), w_price)

                if w['f1'] != "" and w['f1'] != "X":
                    invoice_number=w['f1']
                if not w_id in workbuys.keys():
                    workbuys[w_id] = {
                        'id': w_id,
                        'created_at': w_date,
                        'customer_id': cust_id,
                        'organization_id': org_id,
                        'orders': []
                    }
                workbuys[w_id]['orders'].append({
                    'created_at': w_date,
                    'provider_id': prov_id,
                    'taxpayer_id': tp_id,
                    'claimant_id': empl_id,
                    'invoice_number': invoice_number,
                    'include_iva': w_iva,
                    'discount': discount,
                    'comment': comment,
                    'order_unregisteredproducts': order_unregisteredproducts,
                    'order_provider_products': order_provider_products
                })
                # providers.add(w['Proveedor'])
                # taxpayers.add(w['RAZON SOCIAL'])
                # customers.add(w['EMPRESA'])
                # organizations.add((w['ORG'], w["OC"][0]))
                # employees.add(w['COMPRA'])
                # invoices.add(w['Factura'])
            else:
                # print(w)
                failures += 1

    print(failures)

    if not dry_run:
        for w_id, wb in workbuys.items():
            await create(WorkBuySerializer, **wb)
    else:
        import pdb; pdb.set_trace()
    await Tortoise.close_connections()

asyncio.run(main())