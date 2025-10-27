import os
import re
from typing import Any, Dict, List

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "password")


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def fetch_table_schema() -> Dict[str, Any]:
    """Return the first table schema stored in Neo4j."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        record = session.run(
            """
            MATCH (tb:Table)<-[:HAS_TABLE]-(:Dataset)
            OPTIONAL MATCH (tb)-[:HAS_COLUMN]->(c:Column)
            RETURN tb.fqdn AS fqdn,
                   tb.name AS tname,
                   collect(
                       CASE
                           WHEN c IS NULL THEN NULL
                           ELSE {name:c.name, data_type:c.data_type, description:c.description, aliases:coalesce(c.aliases, [])}
                       END
                   ) AS cols
            LIMIT 1
            """
        ).single()
    driver.close()
    if record is None:
        raise ValueError("No table schema found in Neo4j")
    columns = [col for col in record["cols"] if col is not None]
    return {"fqdn": record["fqdn"], "name": record["tname"], "columns": columns}


def search_columns_by_hint(hint: str, columns: List[Dict[str, Any]]) -> List[str]:
    """Return column names ranked by fuzzy match against a hint."""
    normalized_hint = _normalize(hint)
    ranked: List[tuple[int, str]] = []
    for column in columns:
        score = 0
        if _normalize(column["name"]) in normalized_hint:
            score += 2
        aliases = column.get("aliases") or []
        if any(_normalize(alias) in normalized_hint for alias in aliases):
            score += 1
        description = column.get("description")
        if description and _normalize(description) in normalized_hint:
            score += 1
        if score > 0:
            ranked.append((score, column["name"]))
    ranked.sort(reverse=True)
    return [column_name for _, column_name in ranked]

