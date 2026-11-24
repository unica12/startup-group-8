"""Обновление таблиц Этапа 2.1 без переписывания исторических чеков."""
from sqlalchemy import inspect, text


async def add_receipt_details(conn) -> None:
    postgres = conn.dialect.name == "postgresql"
    schema = "public" if postgres else None
    prefix = "public." if postgres else ""
    draft_type = "uuid" if postgres else "char(32)"
    fields = {
        "receipts": {
            "draft_id": f"{draft_type} REFERENCES {prefix}receipt_drafts(id)",
            "discount": "double precision",
            "price_comparable": "boolean",
        },
        "items": {
            "raw_name": "varchar(256)", "brand": "varchar(128)", "unit": "varchar(2)",
            "discount": "double precision", "package_size": "double precision", "package_unit": "varchar(2)",
        },
    }
    for table, additions in fields.items():
        columns = await conn.run_sync(lambda sync: inspect(sync).get_columns(table, schema=schema))
        existing = {column["name"]: column for column in columns}
        for name, definition in additions.items():
            if name not in existing:
                await conn.execute(text(f"ALTER TABLE {prefix}{table} ADD COLUMN {name} {definition}"))
        if postgres and table == "items":
            for name in ("quantity", "price"):
                if not existing[name]["nullable"]:
                    await conn.execute(text(f"ALTER TABLE public.items ALTER COLUMN {name} DROP NOT NULL"))
    await conn.execute(text(f"CREATE UNIQUE INDEX IF NOT EXISTS ix_receipts_draft_id ON {prefix}receipts (draft_id)"))
