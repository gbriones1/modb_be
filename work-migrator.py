import asyncio
import csv
from datetime import datetime

from tortoise import Tortoise

from main.api.schemas import CustomerSerializer, EmployeeSerializer, OrganizationSerializer, ProductSerializer, TaxPayerSerializer, WorkBuySerializer, WorkSerializer
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
    #     print('error')
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

    works = {}

    failures = 0

    with open('works.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)
        for row in list(reader)[3:]:
            w = dict(zip(headers, row))
            if w.get('HOJA', "") and w.get('TALLER', ""):
                w_number = w['HOJA']
                if isfloat(w['FECHA']):
                    w_date = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(w['FECHA']) - 2)
                elif w['FECHA']:
                    # w_date = datetime.strptime(w['FECHA'], '%d/%m/%Y %H:%M:%S')
                    w_date = datetime.strptime(w['FECHA'], '%d/%m/%Y')
                unit = w.get('UNIDAD')
                model = w.get('TIPO/MARCA')
                invoice_number = None
                invoice_date = None
                cust_id = None
                org_id = None
                tp_id = None
                w_price = 0.0
                wb_id = w.get('OC', "-")
                if "-" in wb_id:
                    wb_id = wb_id.split("-")[1]
                if isfloat(wb_id):
                    wb_id = int(wb_id)
                else:
                    wb_id = None
                payments = []
                work_products = []
                work_unregisteredproducts = []
                work_employees = []
                customer_query = await filter_by(CustomerSerializer, name=w['EMPRESA:'] if w['EMPRESA:'] else 'DESCONOCIDO')
                if customer_query:
                    cust_id = customer_query[0].id
                elif not dry_run:
                    cust_id = (await create(CustomerSerializer, name=w['EMPRESA:'] if w['EMPRESA:'] else 'DESCONOCIDO')).id
                organization_query = await filter_by(OrganizationSerializer, name=w["TALLER"])
                if organization_query:
                    org_id = organization_query[0].id
                elif not dry_run:
                    try:
                        org_id = (await create(OrganizationSerializer, name=w['TALLER'], prefix=w["OC"][0])).id
                    except Exception as e:
                        import pdb; pdb.set_trace()
                        raise e
                tp_name = w['RAZONSOCIAL'] if w['RAZONSOCIAL'] else 'MUELLES OBRERO'
                if tp_name == "MUELLESOBRERO" or tp_name == "MUELLES":
                    tp_name = "MUELLES OBRERO"
                elif tp_name == "JORGECRISTO":
                    tp_name = "JORGE CRISTO"
                taxpayer_query = await filter_by(TaxPayerSerializer, name=tp_name)
                if taxpayer_query:
                    tp_id = taxpayer_query[0].id
                elif not dry_run:
                    tp_id = (await create(TaxPayerSerializer, name=tp_name, key=tp_name[:4]+'010195XYZ')).id
                workbuy_query = await filter_by(WorkBuySerializer, id=wb_id)
                if not workbuy_query:
                    wb_id = None
                for i in range(24):
                    if isfloat(w.get('cant'+str(i+1), "")) and isfloat(w.get('precio'+str(i+1), "")):
                        w_price += (float(w['precio'+str(i+1)])*int(w['cant'+str(i+1)]))
                        if w['cod'+str(i+1)]:
                            product_query = await filter_by(ProductSerializer, code=w["cod"+str(i+1)])
                            if product_query:
                                work_products.append({
                                    'product_id': product_query[0].id,
                                    'amount': int(w['cant'+str(i+1)]),
                                    'price': float(w['precio'+str(i+1)]),
                                })
                            else:
                                work_unregisteredproducts.append({
                                    'code': w['cod'+str(i+1)],
                                    'description': w['refa'+str(i+1)],
                                    'amount': int(w['cant'+str(i+1)]),
                                    'price': float(w['precio'+str(i+1)]),
                                })
                        else:
                            work_unregisteredproducts.append({
                                'code': "",
                                'description': w['refa'+str(i+1)],
                                'amount': int(w['cant'+str(i+1)]),
                                'price': float(w['precio'+str(i+1)]),
                            })
                for i in range(3):
                    emp = w.get("T"+str(i+1))
                    if emp:
                        employee_query = await filter_by(EmployeeSerializer, name=emp)
                        emp_id = None
                        if employee_query:
                            emp_id = employee_query[0].id
                        elif not dry_run:
                            emp_id = (await create(EmployeeSerializer, name=emp)).id
                        work_employees.append({
                            "employee_id": emp_id
                        })
                w_price = float("{:.2f}".format(w_price))
                iva = None
                if isfloat(w.get('16%IVA')):
                    iva = float("{:.2f}".format(float(w.get('16%IVA'))))
                w_iva = True if iva else False
                
                if w.get('NoFactura') and isfloat(w.get('NoFactura')) and int(w.get('NoFactura')):
                    invoice_number = int(w.get('NoFactura'))
                    if isfloat(w['FECHAFACT']):
                        invoice_date = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(w['FECHAFACT']) - 2)
                    elif w['FECHAFACT']:
                        # w_date = datetime.strptime(w['FECHAFACT'], '%d/%m/%Y %H:%M:%S')
                        try:
                            invoice_date = datetime.strptime(w['FECHAFACT'], '%d/%m/%Y')
                        except:
                            invoice_date = datetime.strptime(w['FECHAFACT'], '%m/%d/%Y')

                if w.get('Cantidadpagada') and isfloat(w.get('Cantidadpagada')) and float(w.get('Cantidadpagada')):
                    method = w.get('Formadepago')
                    if method.startswith('CRE'):
                        method = 'r'
                    elif method == 'CHEQUE':
                        method = 'k'
                    elif method == 'TARJETA':
                        method = 'd'
                    elif method == 'GARANTIA':
                        method = 'w'
                    elif method.startswith('TRA'):
                        method = 't'
                    else:
                        method = 'c'
                    payment_date = None
                    if isfloat(w['FECHAPAGO']):
                        payment_date = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(w['FECHAPAGO']) - 2)
                    elif w['FECHAPAGO']:
                        # w_date = datetime.strptime(w['FECHAPAGO'], '%d/%m/%Y %H:%M:%S')
                        payment_date = datetime.strptime(w['FECHAPAGO'], '%d/%m/%Y')
                    payments = [{
                        'amount': float(w.get('Cantidadpagada')),
                        'method': method,
                        'date': payment_date
                    }]


                # impo = 0.0
                # if isfloat(w.get('IMPORETE')):
                #     impo = float("{:.2f}".format(float(w.get('IMPORETE'))))
                # if not w_price == impo:
                #     print(w_id)
                #     print(w_price == impo, w.get('IMPORETE'), w_price)

                if not w_number in works.keys():
                    works[w_number] = {
                        'number': w_number,
                        'unit': unit,
                        'model': model,
                        'created_at': w_date,
                        'customer_id': cust_id,
                        'organization_id': org_id,
                        'taxpayer_id': tp_id,
                        'work_products': work_products,
                        'work_unregisteredproducts': work_unregisteredproducts,
                        'work_employees': work_employees,
                        'workbuy_id': wb_id,
                        'include_iva': w_iva,
                        'invoice_number': invoice_number,
                        'invoice_date': invoice_date,
                        'payments': payments,
                    }
                    if invoice_number and invoice_date:
                        works[w_number]['has_invoice'] = True
                else:
                    print("Repeated ID", wb_id)
                    failures += 1
                # providers.add(w['Proveedor'])
                # taxpayers.add(w['RAZON SOCIAL'])
                # customers.add(w['EMPRESA'])
                # organizations.add((w['ORG'], w["OC"][0]))
                # employees.add(w['COMPRA'])
                # invoices.add(w['Factura'])
            else:
                print("No number", w)
                failures += 1

    print(failures)

    if not dry_run:
        for w_id, wb in works.items():
            await create(WorkSerializer, **wb)

    # import pdb; pdb.set_trace()
    await Tortoise.close_connections()

asyncio.run(main())