-- SELECT nextval(pg_get_serial_sequence('provider', 'id'));

-- For products migrator
SELECT setval('appliance_id_seq', COALESCE((SELECT MAX(id)+1 FROM appliance), 1), false);
SELECT setval('brand_id_seq', COALESCE((SELECT MAX(id)+1 FROM brand), 1), false);
SELECT setval('provider_id_seq', COALESCE((SELECT MAX(id)+1 FROM provider), 1), false);
SELECT setval('product_id_seq', COALESCE((SELECT MAX(id)+1 FROM product), 1), false);
SELECT setval('percentage_id_seq', COALESCE((SELECT MAX(id)+1 FROM percentage), 1), false);

-- For workbuys
SELECT setval('workbuy_id_seq', COALESCE((SELECT MAX(id)+1 FROM workbuy), 1), false);

-- For workbuys migrator
-- SELECT setval('customer_id_seq', COALESCE((SELECT MAX(id)+1 FROM customer), 1), false);
-- SELECT setval('organization_id_seq', COALESCE((SELECT MAX(id)+1 FROM organization), 1), false);
-- SELECT setval('provider_id_seq', COALESCE((SELECT MAX(id)+1 FROM provider), 1), false);
-- SELECT setval('taxpayer_id_seq', COALESCE((SELECT MAX(id)+1 FROM taxpayer), 1), false);
-- SELECT setval('employee_id_seq', COALESCE((SELECT MAX(id)+1 FROM employee), 1), false);
-- SELECT setval('workbuy_id_seq', COALESCE((SELECT MAX(id)+1 FROM workbuy), 1), false);

-- -- For works migrator
-- SELECT setval('customer_id_seq', COALESCE((SELECT MAX(id)+1 FROM customer), 1), false);
-- SELECT setval('organization_id_seq', COALESCE((SELECT MAX(id)+1 FROM organization), 1), false);
-- SELECT setval('taxpayer_id_seq', COALESCE((SELECT MAX(id)+1 FROM taxpayer), 1), false);
-- SELECT setval('employee_id_seq', COALESCE((SELECT MAX(id)+1 FROM employee), 1), false);
-- SELECT setval('work_id_seq', COALESCE((SELECT MAX(id)+1 FROM work), 1), false);