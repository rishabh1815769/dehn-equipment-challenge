### DEHN Equipment Challenge – Graph prep (pre-Postgres steps)

This document captures everything we set up in the repository before introducing PostgreSQL as the system of record. It includes data cleaning, CSV preparation, and Neo4j imports you can reproduce end-to-end.

### Branch
- Working branch: `feature/add-equipment-categories`

### Dataset A: Building blocks (components) → Neo4j
Files and scripts added:
- `scripts/prepare_staging.py`
  - Reads `building_blocks_cleaned.csv` and produces tidy staging CSVs with an EAV model for properties.
  - Keeps property names exactly as in CSV; extracts units only to the relationship property.
  - Outputs in `staging/`: `components.csv`, `manufacturers.csv`, `categories.csv`, `properties.csv`, `component_manufacturer.csv`, `component_category.csv`, `component_properties.csv`.

- Neo4j Cypher (Dataset A):
  - `neo4j/constraints.cypher`: uniqueness on `:Component(id)`, `:Category(name)`, `:Manufacturer(name)`, `:Property(name)`; optional full-text index for components (may be skipped if procedure is unavailable).
  - `neo4j/import_http.cypher`: HTTP `LOAD CSV` import (Neo4j 5 syntax used where supported). If `CALL { … } IN TRANSACTIONS` is not available, run the statements individually.

How to regenerate staging CSVs locally:
```bash
python3 scripts/prepare_staging.py --input building_blocks_cleaned.csv --out staging
```

Import (via Browser) using public CSVs on this branch:
- Open Neo4j Browser and run:
  - `neo4j/constraints.cypher`
  - `neo4j/import_http.cypher`

Example graph queries (Dataset A):
```cypher
MATCH (c:Component)-[:IN_CATEGORY]->(cat:Category)
RETURN cat, c LIMIT 200;

MATCH (c:Component)-[r:HAS_PROPERTY]->(:Property {name:'Load capacity [kg]'})
WHERE r.numeric_value >= 6
RETURN c.type, r.numeric_value, r.unit;
```

### Dataset B: Solutions graph (V2) – files and imports
Location: `euipment_version_2/` (parent folder for the V2 solution graph)

CSV inputs (source vs generated):
- Provided (source):
  - `euipment_version_2/solutions.csv` – cleaned to remove a leading blank line; headers preserved (German).
  - `euipment_version_2/modules.csv` – cleaned: removed `Baukasten!` placeholder rows; deduplicated by ID.
  - `euipment_version_2/solution_modules.csv` – wide matrix kept as reference.
- Generated (from source):
  - `euipment_version_2/solution_parts.csv` – parent→child (MAIN→PARTIAL) with `qty=1`.
  - `euipment_version_2/solution_modules_edges.csv` – long edge list `solution_id,module_id,qty,role`.
    - Duplicate header "Etikett applizieren" disambiguated as `Etikett applizieren_1` and `_2`.
    - `#REF!` columns/values dropped.

Neo4j V2 scripts:
- `euipment_version_2/neo4j/constraints_v2.cypher`
  - Unique constraints: `:SolutionV2(id)`, `:ModuleV2(id)` and also for styling labels `:MainSolutionV2(id)`, `:PartialSolutionV2(id)`.
- `euipment_version_2/neo4j/import_http_v2_simple.cypher`
  - HTTP `LOAD CSV` import for: `solutions.csv`, `modules.csv`, `solution_parts.csv`, `solution_modules_edges.csv`.
  - Enforces hierarchy rule: skip `USES_MODULE` from MAIN solutions that have children (modules hang under PARTIALs); allow direct modules for MAINs without children.
  - After loading solutions, assigns sublabels `:MainSolutionV2` / `:PartialSolutionV2` and removes generic `:SolutionV2` so you can color nodes by label easily.

How to import (Dataset B):
1) In Browser (or cypher-shell) run:
   - `euipment_version_2/neo4j/constraints_v2.cypher`
   - `euipment_version_2/neo4j/import_http_v2_simple.cypher`
2) Optional styling:
   - Color by label: `MainSolutionV2` (blue), `PartialSolutionV2` (orange), `ModuleV2` (green).
   - Or set captions to `name`.

Example V2 graph queries:
```cypher
// Full tree: MAINs with PARTIALs + modules
MATCH p1=(m:MainSolutionV2)-[:HAS_PART*0..3]->(s:PartialSolutionV2)
OPTIONAL MATCH p2=(s)-[:USES_MODULE]->(mod:ModuleV2)
RETURN p1, p2 LIMIT 2000;

// Include MAINs without children (direct modules)
MATCH (m:MainSolutionV2)
OPTIONAL MATCH p1=(m)-[:HAS_PART]->(ps:PartialSolutionV2)
OPTIONAL MATCH p2=(ps)-[:USES_MODULE]->(mod1:ModuleV2)
OPTIONAL MATCH p3=(m)-[:USES_MODULE]->(mod2:ModuleV2)
RETURN m, p1, p2, p3 LIMIT 2000;
```

### Notes
- All imports use raw GitHub URLs from `feature/add-equipment-categories`; you can also run locally by copying CSVs into Neo4j's import directory and switching `LOAD CSV` to `file:///`.
- We added `kind` and `uiColor` properties once for convenient Browser styling; the preferred longer-term approach is styling by label (`MainSolutionV2`, `PartialSolutionV2`, `ModuleV2`).

This completes all pre‑Postgres setup and imports. The PostgreSQL schema and sync come next (documented separately).