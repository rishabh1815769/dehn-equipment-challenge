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

### AI-assisted search and data understanding (hackathon add-on)
- Built a lightweight custom UI on top of OpenSearch (Enterprise Search) to index our CSVs, notes, and generated artifacts.
- Implemented context learning via retrieval-augmented prompting: the UI retrieves relevant snippets (schema, examples, mappings) and injects them into prompts to Gemini, so answers are grounded in our data.
- Prompt engineering highlights:
  - System primer with our domain vocabulary (MAIN/PARTIAL, HAS_PART, USES_MODULE) and CSV headers.
  - Few-shot templates for Cypher generation and data QA.
  - Guardrails to prefer factual, source-cited outputs.
- Outcomes:
  - Natural-language Q&A about solutions/modules and their relationships.
  - One-click generation of Cypher queries for Browser.
  - Faster validation loops (e.g., “show MAINs with children and their modules”, “find CPU modules”).
- Why it helped in a hackathon:
  - Rapid onboarding for team members.
  - Consistent, grounded answers tied to the current repo state and graph schema.
