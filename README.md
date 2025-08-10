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

### Data model and tables (authoritative vs. derived)

- Core (authoritative, persisted in Postgres; drive the graph)
  - solutions: master list of solutions (MAIN/Teilprozess)
  - modules: catalog of modules/components
  - solution_parts: parent→child hierarchy (MAIN→PARTIAL)
  - solution_modules: solution→module BOM edges (qty, role)

- Derived/dependent (computed from core; transient or generated)
  - v_solution_modules_effective (SQL VIEW): filters out direct MAIN→Module where MAIN has children; enforces hierarchy policy upstream of the graph
  - CSV artifacts used for graph import (at repo root):
    - solutions.csv (source)
    - modules.csv (source)
    - solution_parts.csv (derived from mapping; qty defaults to 1 if absent)
    - solution_modules_edges.csv (derived long-form edges from the wide matrix; roles preserved; duplicate role headers disambiguated, e.g., Etikett applizieren_1/_2)
  - Neo4j labels/relationships (materialization of core):
    - Labels: MainSolutionV2, PartialSolutionV2, ModuleV2
    - Relationships: HAS_PART (Main→Partial), USES_MODULE (Partial→Module; Main→Module only if Main has no children)

#### Core table schemas (Postgres)

solutions (PK: id)
```
id                BIGINT       NOT NULL PRIMARY KEY
name              TEXT         NOT NULL
type              TEXT         NOT NULL  -- 'Hauptprozess' | 'Teilprozess'
merkmalsklasse_1  TEXT         NULL
merkmalsklasse_2  TEXT         NULL
merkmalsklasse_3  TEXT         NULL
randbedingung_1   TEXT         NULL
randbedingung_2   TEXT         NULL
verknuepfungen_prozessebene   TEXT NULL
verknuepfungen_baukastenebene TEXT NULL
hinweise          TEXT         NULL
ablageort_konstruktiv         TEXT NULL
ablageort_steuerungstechnisch TEXT NULL
ablageort_prueftechnisch      TEXT NULL
ablageort_robotertechnisch    TEXT NULL
updated_at        TIMESTAMPTZ  NOT NULL DEFAULT now()
deleted_at        TIMESTAMPTZ  NULL
```

modules (PK: id)
```
id                BIGINT       NOT NULL PRIMARY KEY
name              TEXT         NOT NULL
version           TEXT         NULL
bauteilkategorie  TEXT         NULL
hersteller        TEXT         NULL
typ               TEXT         NULL
eigenschaft_1     TEXT         NULL
wert_1            TEXT         NULL
eigenschaft_2     TEXT         NULL
wert_2            TEXT         NULL
eigenschaft_3     TEXT         NULL
wert_3            TEXT         NULL
ablageort_konstruktiv         TEXT NULL
ablageort_steuerungstechnisch TEXT NULL
ablageort_prueftechnisch      TEXT NULL
ablageort_robotertechnisch    TEXT NULL
sonstiges          TEXT        NULL
spalte1            TEXT        NULL
updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at         TIMESTAMPTZ NULL
```

solution_parts (PK: parent_solution_id, child_solution_id)
```
parent_solution_id  BIGINT NOT NULL REFERENCES solutions(id) ON UPDATE CASCADE ON DELETE CASCADE
child_solution_id   BIGINT NOT NULL REFERENCES solutions(id) ON UPDATE CASCADE ON DELETE CASCADE
qty                 INT    NOT NULL DEFAULT 1 CHECK (qty > 0)
updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at          TIMESTAMPTZ NULL
```

solution_modules (PK: solution_id, module_id, role)
```
solution_id  BIGINT NOT NULL REFERENCES solutions(id) ON UPDATE CASCADE ON DELETE CASCADE
module_id    BIGINT NOT NULL REFERENCES modules(id)   ON UPDATE CASCADE ON DELETE CASCADE
qty          INT    NOT NULL DEFAULT 1 CHECK (qty > 0)
role         TEXT   NULL       -- functional position, e.g., 'Etikett applizieren_1'
updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at   TIMESTAMPTZ NULL
```

v_solution_modules_effective (VIEW)
```
SELECT sm.solution_id,
       sm.module_id,
       COALESCE(sm.qty,1) AS qty,
       sm.role
FROM solution_modules sm
JOIN solutions s ON s.id = sm.solution_id
LEFT JOIN solution_parts sp ON sp.parent_solution_id = s.id
WHERE NOT (s.type = 'Hauptprozess' AND sp.child_solution_id IS NOT NULL)
  AND sm.deleted_at IS NULL
  AND s.deleted_at  IS NULL;
```

Indexing/constraints
- solutions: PRIMARY KEY(id), index on type
- modules: PRIMARY KEY(id)
- solution_parts: PRIMARY KEY(parent_solution_id, child_solution_id), index on child_solution_id
- solution_modules: PRIMARY KEY(solution_id, module_id, role), index on module_id

Operational notes
- Staging tables (`stg_*`) mirror CSV headers and are used only for bulk load; application logic reads/writes the core tables.
- The hierarchy rule is enforced at two levels for defense-in-depth:
  1) SQL view `v_solution_modules_effective` for exports
  2) Neo4j import script filters USES_MODULE creation when a MAIN has children
 
    ![WhatsApp Image 2025-08-10 at 11 18 59](https://github.com/user-attachments/assets/46cfe152-ffae-4e1e-a362-a5c47d9d379e)

    ![WhatsApp Image 2025-08-10 at 11 29 29](https://github.com/user-attachments/assets/97cf28c2-ac4d-4f60-857e-4664da04599c)


