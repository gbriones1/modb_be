import asyncio
import csv
from datetime import datetime
import pdb

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

async def get_next_wb_id():
    model = WorkBuySerializer.__config__.orig_model
    db_obj = model.all().order_by('-id').first()
    result = await WorkBuySerializer.from_queryset_single(db_obj)
    return result.id + 1

async def get_all(serializer):
    model = serializer.__config__.orig_model
    return await serializer.from_queryset(model.all())

async def filter_by(serializer, **filters):
    model = serializer.__config__.orig_model
    db_obj = model.filter(**filters)
    try:
        return await serializer.from_queryset(db_obj)
    except Exception as e:
        import pdb; pdb.set_trace()
        raise e
    # return await serializer.from_queryset(db_obj)

async def create(serializer, **data):
    model = serializer.__config__.orig_model
    try:
        db_obj = await model.create(**data)
        result = await serializer.from_tortoise_orm(db_obj)
    except Exception as e:
        import pdb; pdb.set_trace()
        raise e
    return result

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
    ups = {}
    ups_count = {}

    failures = 0

    with open('works.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)
        for row in list(reader)[3:]:
            w = dict(zip(headers, row))
            if w.get('HOJA', "") and w.get('TALLER', "") and w['TALLER'] != "0" and w['FECHA'] != 'ERROR':
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
                payments = []
                work_customer_products = []
                work_unregisteredproducts = []
                work_employees = []
                customer_query = await filter_by(CustomerSerializer, name=w['EMPRESA:'] if w['EMPRESA:'] and w['EMPRESA:'] != '0' else 'DESCONOCIDO')
                if customer_query:
                    cust_id = customer_query[0].id
                elif not dry_run:
                    cust_id = (await create(CustomerSerializer, name=w['EMPRESA:'] if w['EMPRESA:'] and w['EMPRESA:'] != '0' else 'DESCONOCIDO')).id
                organization_query = await filter_by(OrganizationSerializer, name=w["TALLER"])
                if organization_query:
                    org_id = organization_query[0].id
                elif not dry_run:
                    try:
                        org_id = (await create(OrganizationSerializer, name=w['TALLER'], prefix=w["OC"][0])).id
                    except Exception as e:
                        # import pdb; pdb.set_trace()
                        raise e
                wb_id = w.get('OC', "-")
                if ("-" in wb_id and isfloat(wb_id.split("-")[1])) or isfloat(wb_id) or (len(wb_id) > 2 and isfloat(wb_id[1:])):
                    if isfloat(wb_id):
                        wb_id = int(wb_id)
                    elif len(wb_id) > 2 and isfloat(wb_id[1:]) and "-" not in wb_id:
                        wb_id = int(wb_id[1:])
                    else:
                        wb_id = int(wb_id.split("-")[1])
                    if wb_id == 0:
                        wb_id = await get_next_wb_id()
                        workbuy_query = None
                    else:
                        workbuy_query = await filter_by(WorkBuySerializer, id=wb_id)
                    if not workbuy_query:
                        wb_data = {
                            'id': wb_id,
                            'created_at': w_date,
                            'customer_id': cust_id,
                            'organization_id': org_id,
                        }
                        if not dry_run:
                            wb_id = (await create(WorkBuySerializer, **wb_data)).id
                        else:
                            wb_id = None
                    else:
                        wb_id = workbuy_query[0].id
                        if workbuy_query[0].customer.id != cust_id or workbuy_query[0].organization.id != org_id:
                            if not dry_run:
                                await update(WorkBuySerializer, wb_id, **{
                                    "customer_id": cust_id,
                                    "organization_id": org_id
                                })
                else:
                    wb_data = {
                        'id': await get_next_wb_id(),
                        'created_at': w_date,
                        'customer_id': cust_id,
                        'organization_id': org_id,
                    }
                    if not dry_run:
                        try:
                            wb_id = (await create(WorkBuySerializer, **wb_data)).id
                        except:
                            failures += 1
                            print("Unable to create WB", w)
                            continue
                    else:
                        wb_id = None
                tp_name = w['RAZONSOCIAL'] if w['RAZONSOCIAL'] else 'MUELLES OBRERO'
                if tp_name == "MUELLESOBRERO" or tp_name == "MUELLES" or tp_name == "0" or tp_name == "ERROR" or tp_name == "830.72" or tp_name == "Muelles Obrero":
                    tp_name = "MUELLES OBRERO"
                elif tp_name == "JORGECRISTO":
                    tp_name = "JORGE CRISTO"
                taxpayer_query = await filter_by(TaxPayerSerializer, name=tp_name)
                if taxpayer_query:
                    tp_id = taxpayer_query[0].id
                elif not dry_run:
                    tp_id = (await create(TaxPayerSerializer, name=tp_name, key=tp_name[:4]+'010195XYZ')).id
                for i in range(24):
                    if isfloat(w.get('cant'+str(i+1), "")) and isfloat(w.get('precio'+str(i+1), "")) and w['refa'+str(i+1)] != "0":
                        w_price += (float(w['precio'+str(i+1)])*int(w['cant'+str(i+1)]))
                        # if w['cod'+str(i+1)]:
                        #     product_query = await filter_by(ProductSerializer, code=w["cod"+str(i+1)])
                        #     if product_query:
                        #         work_products.append({
                        #             'product_id': product_query[0].id,
                        #             'amount': int(w['cant'+str(i+1)]),
                        #             'price': float(w['precio'+str(i+1)]),
                        #         })
                        #     else:
                        #         work_unregisteredproducts.append({
                        #             'code': w['cod'+str(i+1)],
                        #             'description': w['refa'+str(i+1)],
                        #             'amount': int(w['cant'+str(i+1)]),
                        #             'price': float(w['precio'+str(i+1)]),
                        #         })
                        # else:
                        #     work_unregisteredproducts.append({
                        #         'code': "",
                        #         'description': w['refa'+str(i+1)],
                        #         'amount': int(w['cant'+str(i+1)]),
                        #         'price': float(w['precio'+str(i+1)]),
                        #     })
                        product_query = await filter_by(ProductSerializer, code=w['cod'+str(i+1)])
                        if product_query:
                            pp_id = None
                            customer_query = await filter_by(CustomerSerializer, name=w['EMPRESA:'] if w['EMPRESA:'] and w['EMPRESA:'] != '0' else 'DESCONOCIDO')
                            if customer_query:
                                customer = customer_query[0]
                                # import pdb; pdb.set_trace()
                                for pp in customer.customer_products:
                                    if pp.product.id == product_query[0].id:
                                        pp_id = pp.id
                                        break
                            if not pp_id and not dry_run:
                                new_pp = []
                                for pp in customer.customer_products:
                                    new_pp.append({'id': pp.id})
                                new_pp.append({"product_id":product_query[0].id, "price":float(w['precio'+str(i+1)]), "code":product_query[0].code})
                                await update(CustomerSerializer, customer.id, **{"customer_products":new_pp})
                                customer_query = await filter_by(CustomerSerializer, name=w['EMPRESA:'] if w['EMPRESA:'] else 'DESCONOCIDO')
                                for pp in customer_query[0].customer_products:
                                    if pp.product.id == product_query[0].id:
                                        pp_id = pp.id
                                        break
                            if not dry_run and customer and not pp_id:
                                import pdb; pdb.set_trace()
                            work_customer_products.append({
                                'customer_product_id': pp_id,
                                'amount': int(w['cant'+str(i+1)]),
                                'price': float(w['precio'+str(i+1)]),
                            })
                        else:
                            if float(w['precio'+str(i+1)]) < 0.0:
                                discount = float(w['precio'+str(i+1)]) * -1
                            else:
                                if w['cod'+str(i+1)] and w['cod'+str(i+1)] != "0":
                                    if w['cod'+str(i+1)] not in ups_count:
                                        ups_count[w['cod'+str(i+1)]] = 0
                                        ups[w['cod'+str(i+1)]] = set()
                                    ups_count[w['cod'+str(i+1)]] += 1
                                    ups[w['cod'+str(i+1)]].add(w['refa'+str(i+1)])
                                work_unregisteredproducts.append({
                                    'code': w['cod'+str(i+1)],
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
                if w.get('CantidadPagada') and isfloat(w.get('CantidadPagada')) and float(w.get('CantidadPagada')):
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
                    elif w['FECHAPAGO'] and "/" in w['FECHAPAGO']:
                        # w_date = datetime.strptime(w['FECHAPAGO'], '%d/%m/%Y %H:%M:%S')
                        payment_date = datetime.strptime(w['FECHAPAGO'], '%d/%m/%Y')
                    payments = [{
                        'amount': float(w.get('CantidadPagada')),
                        'method': method,
                        'date': payment_date or w_date
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
                        'taxpayer_id': tp_id,
                        'work_customer_products': work_customer_products,
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
                    print("Repeated Folio", wb_id)
                    failures += 1
                # providers.add(w['Proveedor'])
                # taxpayers.add(w['RAZON SOCIAL'])
                # customers.add(w['EMPRESA'])
                # organizations.add((w['ORG'], w["OC"][0]))
                # employees.add(w['COMPRA'])
                # invoices.add(w['Factura'])
            else:
                # print("No number", w)
                failures += 1

    print(failures)

    if not dry_run:
        for w_id, wb in works.items():
            await create(WorkSerializer, **wb)

    # import pdb; pdb.set_trace()
    await Tortoise.close_connections()

asyncio.run(main())