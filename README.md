### DEHN Equipment Challenge – Hackathon Quickstart

Spin up a clean Solutions Graph in Neo4j in minutes. CSVs live at repo root; import scripts live in `neo4j/`.

### What’s here
- `solutions.csv`: Solutions (MAIN/PARTIAL via `Prozessart`)
- `modules.csv`: Modules catalog
- `solution_parts.csv`: MAIN → PARTIAL links (qty)
- `solution_modules_edges.csv`: Solution → Module links (qty, role)

### Import (60 seconds)
1) In Neo4j Browser, run:
   - `neo4j/constraints_v2.cypher`
   - `neo4j/import_http_v2_simple.cypher`
   (Scripts read the CSVs from this branch’s public URLs.)
2) Styling (optional):
   - Color by label: `MainSolutionV2` (blue), `PartialSolutionV2` (orange), `ModuleV2` (green)
   - Caption: `name`

Notes
- The importer enforces: if a MAIN has children, modules attach to its PARTIALs; MAINs without children can have modules directly.
- To import from local files, copy CSVs into Neo4j’s import folder and replace URLs with `file:///...`.

### Example queries (paste in Browser)
- Complete solutions graph (MAINs, PARTIALs, and modules)
```cypher
MATCH p1=(m:MainSolutionV2)-[:HAS_PART*0..3]->(s:PartialSolutionV2)
OPTIONAL MATCH p2=(s)-[:USES_MODULE]->(mod:ModuleV2)
RETURN p1, p2 LIMIT 2000;
```
- Find CPU-related modules
```cypher
MATCH (mod:ModuleV2)
WHERE toLower(mod.name) CONTAINS 'cpu' OR toLower(mod.typ) CONTAINS 'cpu'
RETURN mod.name, mod.typ, mod.hersteller, mod.version LIMIT 25;
```