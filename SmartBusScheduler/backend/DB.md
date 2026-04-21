To expand your PostgreSQL metadata query into a comprehensive database documentation tool, you can retrieve details about tables, columns, indexes, constraints, triggers, functions, views, sequences, and more. Below are optimized queries that provide a full overview of your database structure using PostgreSQL’s system catalogs.

---

## 📊 1. Enhanced Table & Column Metadata
This builds upon your original query and improves foreign key accuracy while keeping it efficient and readable.

```sql
SELECT
    ns.nspname AS schema_name,
    cls.relname AS table_name,
    attr.attnum AS column_position,
    attr.attname AS column_name,
    pg_catalog.format_type(attr.atttypid, attr.atttypmod) AS data_type,
    CASE
        WHEN attr.attidentity <> '' THEN 'IDENTITY'
        WHEN attr.attgenerated <> '' THEN 'GENERATED'
        ELSE ''
    END AS generation_type,
    CASE
        WHEN attr.attnotnull THEN 'NOT NULL'
        ELSE 'NULLABLE'
    END AS nullability,
    COALESCE(pg_get_expr(def.adbin, def.adrelid), '') AS default_value,
    des.description AS column_comment,
    CASE WHEN pk.conname IS NOT NULL THEN 'YES' ELSE 'NO' END AS is_primary_key,
    CASE WHEN uq.conname IS NOT NULL THEN 'YES' ELSE 'NO' END AS is_unique,
    CASE WHEN fk.conname IS NOT NULL THEN 'YES' ELSE 'NO' END AS is_foreign_key,
    ref_ns.nspname AS referenced_schema,
    ref_cls.relname AS referenced_table,
    ref_attr.attname AS referenced_column
FROM pg_attribute attr
JOIN pg_class cls ON cls.oid = attr.attrelid
JOIN pg_namespace ns ON ns.oid = cls.relnamespace
LEFT JOIN pg_attrdef def
       ON def.adrelid = attr.attrelid AND def.adnum = attr.attnum
LEFT JOIN pg_description des
       ON des.objoid = attr.attrelid AND des.objsubid = attr.attnum
LEFT JOIN pg_constraint pk
       ON pk.conrelid = cls.oid
      AND attr.attnum = ANY (pk.conkey)
      AND pk.contype = 'p'
LEFT JOIN pg_constraint uq
       ON uq.conrelid = cls.oid
      AND attr.attnum = ANY (uq.conkey)
      AND uq.contype = 'u'
LEFT JOIN pg_constraint fk
       ON fk.conrelid = cls.oid
      AND attr.attnum = ANY (fk.conkey)
      AND fk.contype = 'f'
LEFT JOIN pg_class ref_cls ON ref_cls.oid = fk.confrelid
LEFT JOIN pg_namespace ref_ns ON ref_ns.oid = ref_cls.relnamespace
LEFT JOIN pg_attribute ref_attr
       ON ref_attr.attrelid = fk.confrelid
      AND ref_attr.attnum = ANY (fk.confkey)
WHERE attr.attnum > 0
  AND NOT attr.attisdropped
  AND cls.relkind = 'r'
  AND ns.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schema_name, table_name, column_position;
```

---

## 📚 2. Index Information
Displays all indexes, their types, and definitions.

```sql
SELECT
    schemaname AS schema_name,
    tablename AS table_name,
    indexname AS index_name,
    indexdef AS index_definition
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename, indexname;
```

---

## 🔗 3. Constraint Summary
Lists all constraints, including primary keys, foreign keys, and checks.

```sql
SELECT
    ns.nspname AS schema_name,
    cls.relname AS table_name,
    con.conname AS constraint_name,
    CASE con.contype
        WHEN 'p' THEN 'PRIMARY KEY'
        WHEN 'f' THEN 'FOREIGN KEY'
        WHEN 'u' THEN 'UNIQUE'
        WHEN 'c' THEN 'CHECK'
        WHEN 'x' THEN 'EXCLUSION'
    END AS constraint_type,
    pg_get_constraintdef(con.oid) AS definition
FROM pg_constraint con
JOIN pg_class cls ON cls.oid = con.conrelid
JOIN pg_namespace ns ON ns.oid = cls.relnamespace
WHERE ns.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schema_name, table_name, constraint_name;
```

---

## ⚡ 4. Trigger Information

```sql
SELECT
    event_object_schema AS schema_name,
    event_object_table AS table_name,
    trigger_name,
    event_manipulation AS event,
    action_timing AS timing,
    action_statement AS trigger_definition
FROM information_schema.triggers
ORDER BY schema_name, table_name, trigger_name;
```

---

## 🧠 5. Functions and Stored Procedures

```sql
SELECT
    n.nspname AS schema_name,
    p.proname AS function_name,
    pg_get_function_identity_arguments(p.oid) AS arguments,
    pg_get_function_result(p.oid) AS return_type,
    l.lanname AS language,
    pg_get_functiondef(p.oid) AS definition
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
JOIN pg_language l ON l.oid = p.prolang
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schema_name, function_name;
```

---

## 👁️ 6. Views and Materialized Views

```sql
SELECT
    schemaname AS schema_name,
    viewname AS object_name,
    definition
FROM pg_views
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')

UNION ALL

SELECT
    schemaname,
    matviewname,
    definition
FROM pg_matviews
ORDER BY schema_name, object_name;
```

---

## 🔢 7. Sequences

```sql
SELECT
    sequence_schema AS schema_name,
    sequence_name,
    data_type,
    start_value,
    minimum_value,
    maximum_value,
    increment,
    cycle_option
FROM information_schema.sequences
ORDER BY schema_name, sequence_name;
```

---

## 💾 8. Table Sizes and Row Estimates

```sql
SELECT
    ns.nspname AS schema_name,
    cls.relname AS table_name,
    pg_size_pretty(pg_total_relation_size(cls.oid)) AS total_size,
    pg_size_pretty(pg_relation_size(cls.oid)) AS table_size,
    pg_size_pretty(pg_indexes_size(cls.oid)) AS indexes_size,
    cls.reltuples::bigint AS estimated_rows
FROM pg_class cls
JOIN pg_namespace ns ON ns.oid = cls.relnamespace
WHERE cls.relkind = 'r'
  AND ns.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(cls.oid) DESC;
```

---

## 📦 9. Database-Level Overview

```sql
SELECT
    datname AS database_name,
    pg_size_pretty(pg_database_size(datname)) AS database_size
FROM pg_database
ORDER BY pg_database_size(datname) DESC;
```

---

## 🚀 10. Unified Database Object Inventory

```sql
SELECT n.nspname AS schema_name, c.relname AS object_name, 'TABLE' AS object_type
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'r'

UNION ALL
SELECT n.nspname, c.relname, 'VIEW'
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'v'

UNION ALL
SELECT n.nspname, c.relname, 'MATERIALIZED VIEW'
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'm'

UNION ALL
SELECT n.nspname, c.relname, 'SEQUENCE'
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'S'

UNION ALL
SELECT n.nspname, p.proname, 'FUNCTION'
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
ORDER BY schema_name, object_type, object_name;
```

---

## 📘 Bonus: Export Schema Documentation
You can export results for documentation:

```bash
psql -U username -d dbname -F $'\t' -A -o schema_report.tsv -c "YOUR_QUERY"
```

Or generate a full schema dump:

```bash
pg_dump -U username -d dbname --schema-only > schema.sql
```

---

## ✅ Summary

| Object Type | Included |
|-------------|----------|
| Tables & Columns | ✅ |
| Primary & Foreign Keys | ✅ |
| Indexes | ✅ |
| Constraints | ✅ |
| Triggers | ✅ |
| Functions & Procedures | ✅ |
| Views & Materialized Views | ✅ |
| Sequences | ✅ |
| Table Sizes & Statistics | ✅ |
| Database Sizes | ✅ |
| Object Inventory | ✅ |

If you'd like, I can combine these into a single data dictionary view or generate an ER diagram script compatible with tools like DBeaver, pgAdmin, or SchemaSpy.V