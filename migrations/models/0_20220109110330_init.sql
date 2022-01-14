-- upgrade --
CREATE TABLE IF NOT EXISTS "role" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(20) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "user" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(20) NOT NULL UNIQUE,
    "full_name" VARCHAR(50),
    "hashed_password" VARCHAR(128) NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "active" INT NOT NULL  DEFAULT 1,
    "is_admin" INT NOT NULL  DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "apimodel" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
);
CREATE TABLE IF NOT EXISTS "appliance" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "brand" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "customer" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "customercontact" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL,
    "department" VARCHAR(100)   DEFAULT '',
    "email" VARCHAR(100)   DEFAULT '',
    "phone" VARCHAR(15)   DEFAULT '',
    "for_quotation" INT NOT NULL  DEFAULT 0,
    "customer_id" INT NOT NULL REFERENCES "customer" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "employee" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "phone" VARCHAR(15)  UNIQUE
);
CREATE TABLE IF NOT EXISTS "organization" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "prefix" VARCHAR(3)  UNIQUE
);
CREATE TABLE IF NOT EXISTS "product" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "code" VARCHAR(30) NOT NULL UNIQUE,
    "name" VARCHAR(200) NOT NULL,
    "description" VARCHAR(255),
    "appliance_id" INT REFERENCES "appliance" ("id") ON DELETE CASCADE,
    "brand_id" INT REFERENCES "brand" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "provider" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "providercontact" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL,
    "department" VARCHAR(100)   DEFAULT '',
    "email" VARCHAR(100)   DEFAULT '',
    "phone" VARCHAR(15)   DEFAULT '',
    "for_orders" INT NOT NULL  DEFAULT 0,
    "provider_id" INT NOT NULL REFERENCES "provider" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "provider_product" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "price" VARCHAR(40) NOT NULL,
    "discount" VARCHAR(40) NOT NULL  DEFAULT 0,
    "product_id" INT REFERENCES "product" ("id") ON DELETE CASCADE,
    "provider_id" INT REFERENCES "provider" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_provider_pr_provide_643e0e" UNIQUE ("provider_id", "product_id")
);
CREATE TABLE IF NOT EXISTS "storagetype" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "storage" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "organization_id" INT NOT NULL REFERENCES "organization" ("id") ON DELETE CASCADE,
    "storagetype_id" INT NOT NULL REFERENCES "storagetype" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_storage_organiz_4a33c0" UNIQUE ("organization_id", "storagetype_id")
);
CREATE TABLE IF NOT EXISTS "storagebuy" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "customer_id" INT REFERENCES "customer" ("id") ON DELETE CASCADE,
    "organization_id" INT NOT NULL REFERENCES "organization" ("id") ON DELETE CASCADE,
    "storage_id" INT NOT NULL REFERENCES "storage" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "taxpayer" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "key" VARCHAR(13) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "workbuy" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "customer_id" INT NOT NULL REFERENCES "customer" ("id") ON DELETE CASCADE,
    "organization_id" INT NOT NULL REFERENCES "organization" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "order" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "authorized" INT NOT NULL  DEFAULT 0,
    "include_iva" INT NOT NULL  DEFAULT 0,
    "discount" VARCHAR(40),
    "state" VARCHAR(1) NOT NULL  DEFAULT 'A' /* cancelled: X\ncreated: A\nrequested: B\nrecieved: C */,
    "comment" TEXT,
    "has_invoice" INT NOT NULL  DEFAULT 0,
    "invoice_number" VARCHAR(30),
    "invoice_uuid" CHAR(36),
    "invoice_date" DATE,
    "due" DATE,
    "claimant_id" INT REFERENCES "employee" ("id") ON DELETE CASCADE,
    "provider_id" INT NOT NULL REFERENCES "provider" ("id") ON DELETE CASCADE,
    "storagebuy_id" INT REFERENCES "storagebuy" ("id") ON DELETE CASCADE,
    "taxpayer_id" INT NOT NULL REFERENCES "taxpayer" ("id") ON DELETE CASCADE,
    "workbuy_id" INT REFERENCES "workbuy" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "orderpayment" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "date" DATE NOT NULL,
    "amount" VARCHAR(40) NOT NULL,
    "method" VARCHAR(1) NOT NULL  DEFAULT 'c' /* cash: c\ntransfer: t\ncheck: k\ncard: d\ncredit: r\nwarrant: w */,
    "order_id" INT NOT NULL REFERENCES "order" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "order_product" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "amount" INT NOT NULL,
    "price" VARCHAR(40) NOT NULL,
    "order_id" INT NOT NULL REFERENCES "order" ("id") ON DELETE CASCADE,
    "provider_product_id" INT NOT NULL REFERENCES "provider_product" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "order_unregisteredproduct" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "code" VARCHAR(30),
    "description" VARCHAR(255) NOT NULL,
    "amount" INT NOT NULL,
    "price" VARCHAR(40),
    "order_id" INT NOT NULL REFERENCES "order" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "work" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "number" VARCHAR(12) NOT NULL,
    "unit" VARCHAR(30),
    "model" VARCHAR(30),
    "authorized" INT NOT NULL  DEFAULT 0,
    "include_iva" INT NOT NULL  DEFAULT 0,
    "discount" VARCHAR(40),
    "state" VARCHAR(1) NOT NULL  DEFAULT 'Q' /* quoted: Q\nrequested: R\nin_progress: P\ncancelled: X\nfinished: F\nwarrant: W */,
    "comment" TEXT,
    "has_invoice" INT NOT NULL  DEFAULT 0,
    "invoice_number" VARCHAR(30),
    "invoice_uuid" CHAR(36),
    "invoice_date" DATE,
    "due" DATE,
    "customer_id" INT NOT NULL REFERENCES "customer" ("id") ON DELETE CASCADE,
    "organization_id" INT NOT NULL REFERENCES "organization" ("id") ON DELETE CASCADE,
    "taxpayer_id" INT REFERENCES "taxpayer" ("id") ON DELETE CASCADE,
    "workbuy_id" INT REFERENCES "workbuy" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "workpayment" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "date" DATE NOT NULL,
    "amount" VARCHAR(40) NOT NULL,
    "method" VARCHAR(1) NOT NULL  DEFAULT 'c' /* cash: c\ntransfer: t\ncheck: k\ncard: d\ncredit: r\nwarrant: w */,
    "work_id" INT NOT NULL REFERENCES "work" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "work_employee" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "employee_id" INT NOT NULL REFERENCES "employee" ("id") ON DELETE CASCADE,
    "work_id" INT NOT NULL REFERENCES "work" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "work_product" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "amount" INT NOT NULL,
    "price" VARCHAR(40) NOT NULL,
    "product_id" INT NOT NULL REFERENCES "product" ("id") ON DELETE CASCADE,
    "work_id" INT NOT NULL REFERENCES "work" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "work_unregisteredproduct" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "code" VARCHAR(30),
    "description" VARCHAR(255) NOT NULL,
    "amount" INT NOT NULL,
    "price" VARCHAR(40),
    "work_id" INT NOT NULL REFERENCES "work" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "user_role" (
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "role_id" INT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE
);
