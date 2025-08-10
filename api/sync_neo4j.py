from typing import Iterable, List, Tuple
from neo4j import GraphDatabase
from .settings import load_settings


settings = load_settings()


def _neo4j_driver():
    return GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))


def upsert_solutions(nodes: List[Tuple[int, str, str]]):
    """Upsert SolutionV2 nodes with sublabels and drop generic label.

    nodes: list of (id, name, type)
    """
    if not nodes:
        return
    cypher = f"""
    UNWIND $rows AS r
    MERGE (s:SolutionV2 {{id: toString(r.id)}})
      SET s.name = r.name,
          s.type = r.type,
          s.dataset = $dataset
    WITH s
    CALL {{ WITH s WHERE s.type='Hauptprozess' SET s:MainSolutionV2 RETURN 1 }}
    CALL {{ WITH s WHERE s.type<>'Hauptprozess' SET s:PartialSolutionV2 RETURN 1 }}
    REMOVE s:SolutionV2
    """
    with _neo4j_driver() as drv:
        with drv.session() as sess:
            sess.run(cypher, rows=[{"id": i, "name": n, "type": t} for i, n, t in nodes], dataset=settings.dataset)


def upsert_modules(nodes: List[Tuple[int, str, str, str]]):
    """Upsert ModuleV2 nodes.

    nodes: list of (id, name, typ, hersteller)
    """
    if not nodes:
        return
    cypher = f"""
    UNWIND $rows AS r
    MERGE (m:ModuleV2 {{id: toString(r.id)}})
      SET m.name = r.name,
          m.typ = r.typ,
          m.hersteller = r.hersteller,
          m.dataset = $dataset
    """
    with _neo4j_driver() as drv:
        with drv.session() as sess:
            sess.run(cypher, rows=[{"id": i, "name": n, "typ": ty, "hersteller": h} for i, n, ty, h in nodes], dataset=settings.dataset)


def upsert_has_part(edges: Iterable[Tuple[int, int, int]]):
    """Upsert HAS_PART relationships: (parent_id, child_id, qty)."""
    rows = list(edges)
    if not rows:
        return
    cypher = f"""
    UNWIND $rows AS r
    MATCH (p:MainSolutionV2 {{id: toString(r.parent)}})
    MATCH (c:PartialSolutionV2 {{id: toString(r.child)}})
    MERGE (p)-[h:HAS_PART]->(c)
      SET h.qty = r.qty,
          h.dataset = $dataset
    """
    data = [{"parent": p, "child": c, "qty": q} for p, c, q in rows]
    with _neo4j_driver() as drv:
        with drv.session() as sess:
            sess.run(cypher, rows=data, dataset=settings.dataset)


def sync_effective_bom(solution_id: int, bom_rows: Iterable[Tuple[int, int, int, str]]):
    """Synchronize USES_MODULE edges for one solution_id to match effective BOM.

    bom_rows: iterable of (solution_id, module_id, qty, role)
    """
    data = [
        {"sid": str(sid), "mid": str(mid), "qty": qty, "role": role}
        for sid, mid, qty, role in bom_rows
    ]
    cypher = f"""
    // Delete stale edges for this solution_id (dataset-scoped)
    MATCH (s {{id: toString($sid)}})-[u:USES_MODULE {{dataset: $dataset}}]->(:ModuleV2)
    WITH s,u
    OPTIONAL MATCH (s)-[u2:USES_MODULE]->(:ModuleV2)
    WHERE (u2) AND NOT EXISTS {{
      WITH s
      UNWIND $rows AS r
      RETURN 1 WHERE toString(r.sid)=s.id AND type(u2)='USES_MODULE' AND endNode(u2).id = toString(r.mid) AND coalesce(u2.role,'') = coalesce(r.role,'')
    }}
    DELETE u2;

    // Upsert required edges
    UNWIND $rows AS r
    MATCH (s {{id: toString(r.sid)}})
    MATCH (m:ModuleV2 {{id: toString(r.mid)}})
    MERGE (s)-[u:USES_MODULE]->(m)
      SET u.qty = r.qty,
          u.role = r.role,
          u.dataset = $dataset
    """
    with _neo4j_driver() as drv:
        with drv.session() as sess:
            sess.run(
                cypher,
                sid=str(solution_id),
                rows=data,
                dataset=settings.dataset,
            )


