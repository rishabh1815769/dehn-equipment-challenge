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

### Example query (paste in Browser)
```cypher
MATCH (m:MainSolutionV2 {dataset:'equipment_solution_v2'})
OPTIONAL MATCH p1=(m)-[:HAS_PART]->(ps:PartialSolutionV2)
OPTIONAL MATCH p2=(ps)-[:USES_MODULE]->(mod1:ModuleV2 {dataset:'equipment_solution_v2'})
OPTIONAL MATCH p3=(m)-[:USES_MODULE]->(mod2:ModuleV2 {dataset:'equipment_solution_v2'})
RETURN m, p1, p2, p3
LIMIT 2000;
```

<img width="1264" height="538" alt="Screenshot 2025-08-10 at 11 16 58" src="https://github.com/user-attachments/assets/707c3545-080a-46cc-b69c-9c8dcf399d35" />
