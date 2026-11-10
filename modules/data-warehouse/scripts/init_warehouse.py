#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按 schema.json 建一个 SQLite 库，可选导入 CSV。

用法：
    python init_warehouse.py --schema schema.json --db data.db
    python init_warehouse.py --schema schema.json --db data.db --csv records=cases.csv
    python init_warehouse.py --schema schema.json --db data.db --dry-run

规则：
- 只建表，不删表、不改已有字段；
- 每张表自动补 source_path、updated_at 两列；
- CSV 导入按列名匹配字段，不认识的列跳过并报告；
- 主键冲突用 REPLACE，等于按主键去重。
"""
import argparse
import csv
import json
import os
import sqlite3
import sys

TYPES = {
    "text": "TEXT",
    "string": "TEXT",
    "integer": "INTEGER",
    "int": "INTEGER",
    "real": "REAL",
    "float": "REAL",
    "boolean": "INTEGER",
    "bool": "INTEGER",
    "date": "TEXT",
}


def load_schema(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "tables" not in data or not isinstance(data["tables"], list):
        raise SystemExit("schema.json 里没有 tables 数组")
    return data


def table_sql(table):
    fields = table.get("fields", [])
    names = [f["name"] for f in fields]
    cols = []
    for f in fields:
        t = TYPES.get(str(f.get("type", "text")).lower(), "TEXT")
        notnull = " NOT NULL" if f.get("required") else ""
        cols.append(f'"{f["name"]}" {t}{notnull}')
    if "source_path" not in names:
        cols.append('"source_path" TEXT')
    if "updated_at" not in names:
        cols.append('"updated_at" TEXT')
    pk = table.get("primary_key")
    if pk:
        cols.append(f'PRIMARY KEY ("{pk}")')
    return f'CREATE TABLE IF NOT EXISTS "{table["name"]}" (\n  ' + ",\n  ".join(cols) + "\n);"


def index_sql(table):
    out = []
    for field in table.get("indexes", []):
        out.append(f'CREATE INDEX IF NOT EXISTS "idx_{table["name"]}_{field}" ON "{table["name"]}" ("{field}");')
    return out


def import_csv(conn, table, csv_path):
    fields = {f["name"] for f in table.get("fields", [])} | {"source_path", "updated_at"}
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        known = [h for h in headers if h in fields]
        unknown = [h for h in headers if h not in fields]
        rows = []
        for row in reader:
            vals = {h: (row.get(h) or None) for h in known}
            vals.setdefault("source_path", os.path.abspath(csv_path))
            rows.append(vals)
        if not rows:
            print(f"  [空] {csv_path}")
            return 0, unknown
        cols = list(rows[0].keys())
        placeholders = ", ".join("?" for _ in cols)
        col_sql = ", ".join(f'"{c}"' for c in cols)
        sql = f'INSERT OR REPLACE INTO "{table["name"]}" ({col_sql}) VALUES ({placeholders})'
        conn.executemany(sql, [[r.get(c) for c in cols] for r in rows])
        conn.commit()
        return len(rows), unknown


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--csv", action="append", default=[], help="表名=CSV路径，可多次")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    schema = load_schema(args.schema)
    tables = {t["name"]: t for t in schema["tables"]}

    print(f"schema: {args.schema}  version={schema.get('version')}")
    print(f"db:     {args.db}")
    print("-" * 60)
    for t in schema["tables"]:
        print(f"表 {t['name']}：{len(t.get('fields', []))} 个字段，主键 {t.get('primary_key') or '无'}")
        print(table_sql(t))
        for s in index_sql(t):
            print(s)

    if args.dry_run:
        print("\n（dry-run，没有写文件）")
        return 0

    os.makedirs(os.path.dirname(os.path.abspath(args.db)), exist_ok=True)
    conn = sqlite3.connect(args.db)
    try:
        for t in schema["tables"]:
            conn.execute(table_sql(t))
            for s in index_sql(t):
                conn.execute(s)
        conn.commit()
        print("\n建表完成。")
        for item in args.csv:
            if "=" not in item:
                print(f"[跳过] --csv 要写成 表名=路径：{item}")
                continue
            name, path = item.split("=", 1)
            if name not in tables:
                print(f"[跳过] 没有这张表：{name}")
                continue
            if not os.path.isfile(path):
                print(f"[跳过] 找不到文件：{path}")
                continue
            n, unknown = import_csv(conn, tables[name], path)
            print(f"[导入] {name} <- {path}：{n} 行")
            if unknown:
                print(f"        跳过的列：{', '.join(unknown)}")
    finally:
        conn.close()
    print("完成。")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
