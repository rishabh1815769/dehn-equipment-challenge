### DEHN Equipment Challenge – Solutions Graph (current repo layout)

This README reflects the present structure (CSVs at repo root, Neo4j scripts in `neo4j/`). It documents how to load the graph in Neo4j and explore it.

### Branch
- Working branch: `feature/add-equipment-categories`

### CSVs (source for the graph)
- `solutions.csv` – Solutions master (German headers; MAIN/PARTIAL via `Prozessart`)
- `modules.csv` – Modules catalog (German headers)
- `solution_parts.csv` – MAIN → PARTIAL mapping (parent_solution_id, child_solution_id, qty)
- `solution_modules_edges.csv` – Solution → Module edges (solution_id, module_id, qty, role)

### Neo4j import scripts (V2)
- `neo4j/constraints_v2.cypher` – uniqueness:
  - `:SolutionV2(id)`, `:ModuleV2(id)`; also `:MainSolutionV2(id)`, `:PartialSolutionV2(id)` for styling
- `neo4j/import_http_v2_simple.cypher` – HTTP `LOAD CSV` import for the four CSVs, including:
  - Hierarchy rule: if a MAIN has children, skip direct `USES_MODULE` on the MAIN (modules hang under PARTIALs)
  - Assign sublabels `:MainSolutionV2` / `:PartialSolutionV2`, then drop generic `:SolutionV2` for clear coloring

Note: The script reads CSVs from the public GitHub raw URLs on this branch. If you want local file import, copy the CSVs to Neo4j’s import directory and replace the URLs with `file:///...` equivalents.

### How to import
1) Open Neo4j Browser (or use cypher-shell) and run:
   - `neo4j/constraints_v2.cypher`
   - `neo4j/import_http_v2_simple.cypher`
2) Styling (Neo4j Browser → Styling pane):
   - Color by label: `MainSolutionV2` (blue), `PartialSolutionV2` (orange), `ModuleV2` (green)
   - Caption: `name` for all three labels

### Example graph queries
- MAINs with PARTIALs and their modules
```cypher
MATCH p1=(m:MainSolutionV2)-[:HAS_PART*0..3]->(s:PartialSolutionV2)
OPTIONAL MATCH p2=(s)-[:USES_MODULE]->(mod:ModuleV2)
RETURN p1, p2 LIMIT 2000;
```
- Include MAINs without children (direct modules)
```cypher
MATCH (m:MainSolutionV2)
OPTIONAL MATCH p1=(m)-[:HAS_PART]->(ps:PartialSolutionV2)
OPTIONAL MATCH p2=(ps)-[:USES_MODULE]->(mod1:ModuleV2)
OPTIONAL MATCH p3=(m)-[:USES_MODULE]->(mod2:ModuleV2)
RETURN m, p1, p2, p3 LIMIT 2000;
```
- Properties on a component/module (table view)
```cypher
MATCH (m:ModuleV2)
WHERE toLower(m.name) CONTAINS 'cpu'
RETURN m.name, m.typ, m.hersteller, m.version LIMIT 25;
```

### Notes
- The CSV headers are preserved (German) and mapped directly in the import script.
- If you modify CSVs, commit them and re-run the two Cypher scripts to refresh the graph.
- Prior component dataset scripts/files were removed from the repo; this README focuses on the Solutions Graph flow now present in the codebase.