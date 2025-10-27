import json
import os
from neo4j import GraphDatabase
from pathlib import Path

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "password")


def load_schema(schema_path: str) -> None:
    """Load schema metadata into Neo4j graph."""
    with open(schema_path) as f:
        schema = json.load(f)

    dataset = schema["dataset"]
    table = schema["table"]

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        session.run(
            """
            MERGE (d:Dataset {name:$dataset})
            MERGE (tb:Table {fqdn:$fqdn})
              ON CREATE SET tb.name=$tname
              ON MATCH  SET tb.name=$tname
            MERGE (d)-[:HAS_TABLE]->(tb)
            """,
            dataset=dataset,
            fqdn=table["fqdn"],
            tname=table["name"],
        )

        for column in table["columns"]:
            session.run(
                """
                MATCH (tb:Table {fqdn:$fqdn})
                MERGE (col:Column {name:$name, tableFqdn:$fqdn})
                  ON CREATE SET col.data_type=$dtype,
                                col.description=$description,
                                col.aliases=$aliases
                  ON MATCH  SET col.data_type=$dtype,
                                col.description=$description,
                                col.aliases=$aliases
                MERGE (tb)-[:HAS_COLUMN]->(col)
                """,
                fqdn=table["fqdn"],
                name=column["name"],
                dtype=column["data_type"],
                description=column.get("description", ""),
                aliases=column.get("aliases", []),
            )
    driver.close()


if __name__ == "__main__":
    default_schema = Path(__file__).resolve().parent / "schema.json"
    schema_arg = os.getenv("SCHEMA_PATH", str(default_schema))
    load_schema(os.path.abspath(schema_arg))
    print("Schema loaded into Neo4j ✅")

