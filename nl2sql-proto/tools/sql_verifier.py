from typing import Dict, List

import duckdb

DUCK_TYPES = {
    "INTEGER": "INTEGER",
    "INT": "INTEGER",
    "BIGINT": "BIGINT",
    "TEXT": "TEXT",
    "VARCHAR": "VARCHAR",
    "DECIMAL(18,2)": "DECIMAL(18,2)",
    "DOUBLE": "DOUBLE",
    "FLOAT": "DOUBLE",
    "TIMESTAMP": "TIMESTAMP",
    "DATE": "DATE",
}


def verify_sql(sql: str, table: str, columns: List[Dict]) -> Dict[str, str | bool]:
    """Validate SQL syntax and column references against DuckDB."""
    connection = duckdb.connect(database=":memory:")
    column_defs = ", ".join(
        [
            f'"{column["name"]}" {DUCK_TYPES.get(column["data_type"].upper(), "TEXT")}'
            for column in columns
        ]
    )
    if not column_defs:
        raise ValueError("No columns provided for verification")
    connection.execute(f'CREATE TABLE "{table}" ({column_defs});')
    try:
        connection.execute("EXPLAIN " + sql)
        return {"ok": True, "message": "SQL parsed and planned successfully"}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}
    finally:
        connection.close()

