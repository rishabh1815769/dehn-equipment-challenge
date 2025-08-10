import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    postgres_dsn: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    dataset: str = "equipment_solution_v2"


def load_settings() -> Settings:
    return Settings(
        postgres_dsn=os.environ.get(
            "POSTGRES_DSN",
            "postgresql+psycopg2://dehn-equipment-db-user:%25%3EL%7D*aKo%3Dh%25n8pM5@34.159.55.236:5432/equipment_solution_v2?sslmode=require",
        ),
        neo4j_uri=os.environ.get("NEO4J_URI", "bolt://35.232.36.161:7687"),
        neo4j_user=os.environ.get("NEO4J_USER", "neo4j"),
        neo4j_password=os.environ.get("NEO4J_PASSWORD", "StartNeo4J*"),
    )


