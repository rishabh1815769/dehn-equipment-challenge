// Simple LOAD CSV import for V2 dataset (no CALL { } IN TRANSACTIONS)

// Solutions
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/euipment_version_2/solutions.csv' AS r
WITH r WHERE r.Prozessnummer IS NOT NULL AND r.Prozessnummer <> ''
MERGE (s:SolutionV2 {id: r.Prozessnummer})
SET s.dataset = 'equipment_solution_v2',
    s.name = r.Prozessname,
    s.type = r.Prozessart,
    s.`Merkmalsklasse 1` = r.`Merkmalsklasse 1`,
    s.`Merkmalsklasse 2` = r.`Merkmalsklasse 2`,
    s.`Merkmalsklasse 3` = r.`Merkmalsklasse 3`,
    s.`Randbedingung 1` = r.`Randbedingung 1`,
    s.`Randbedingung 2` = r.`Randbedingung 2`,
    s.`Verknüpfungen Prozessebene` = r.`Verknüpfungen Prozessebene`,
    s.`Verknüpfungen Baukastenebene` = r.`Verknüpfungen Baukastenebene`,
    s.`Hinweise` = r.`Hinweise`,
    s.`Ablageort konstruktiv` = r.`Ablageort konstruktiv`,
    s.`Ablageort steuerungstechnisch` = r.`Ablageort steuerungstechnisch`,
    s.`Ablageort prüftechnisch` = r.`Ablageort prüftechnisch`,
    s.`Ablageort robotertechnisch` = r.`Ablageort robotertechnisch`;

// Assign sublabels for styling and drop generic label
MATCH (s:SolutionV2 {dataset:'equipment_solution_v2'}) WHERE s.type='Hauptprozess' SET s:MainSolutionV2;
MATCH (s:SolutionV2 {dataset:'equipment_solution_v2'}) WHERE s.type<>'Hauptprozess' SET s:PartialSolutionV2;
MATCH (s:SolutionV2 {dataset:'equipment_solution_v2'}) REMOVE s:SolutionV2;

// Modules
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/euipment_version_2/modules.csv' AS r
WITH r WHERE r.`Lfd. Nummer` IS NOT NULL AND r.`Lfd. Nummer` <> ''
MERGE (m:ModuleV2 {id: r.`Lfd. Nummer`})
SET m.dataset = 'equipment_solution_v2',
    m.name = r.`Bauteilnamen`,
    m.version = r.`Version`,
    m.`Bauteilkategorie` = r.`Bauteilkategorie`,
    m.`Hersteller` = r.`Hersteller`,
    m.`Typ` = r.`Typ`,
    m.`Eigenschaft 1` = r.`Eigenschaft 1`,
    m.`Wert 1` = r.`Wert 1`,
    m.`Eigenschaft 2` = r.`Eigenschaft 2`,
    m.`Wert 2` = r.`Wert 2`,
    m.`Eigenschaft 3` = r.`Eigenschaft 3`,
    m.`Wert 3` = r.`Wert 3`,
    m.`Ablageort konstruktiv` = r.`Ablageort konstruktiv`,
    m.`Ablageort steuerungstechnisch` = r.`Ablageort steuerungstechnisch`,
    m.`Ablageort prüftechnisch` = r.`Ablageort prüftechnisch`,
    m.`Ablageort robotertechnisch` = r.`Ablageort robotertechnisch`,
    m.`Sonstiges:` = r.`Sonstiges:`,
    m.`Spalte1` = r.`Spalte1`;

// HAS_PART
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/euipment_version_2/solution_parts.csv' AS r
WITH r WHERE r.parent_solution_id IS NOT NULL AND r.child_solution_id IS NOT NULL AND r.parent_solution_id <> '' AND r.child_solution_id <> ''
MATCH (p:SolutionV2 {id: r.parent_solution_id})
MATCH (c:SolutionV2 {id: r.child_solution_id})
MERGE (p)-[h:HAS_PART]->(c)
SET h.dataset = 'equipment_solution_v2',
    h.qty = CASE WHEN r.qty IS NULL OR r.qty = '' THEN 1 ELSE toInteger(r.qty) END;

// USES_MODULE with MAIN/children skip rule
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/euipment_version_2/solution_modules_edges.csv' AS r
WITH r WHERE r.solution_id IS NOT NULL AND r.solution_id <> '' AND r.module_id IS NOT NULL AND r.module_id <> ''
MATCH (s:SolutionV2 {id: r.solution_id})
MATCH (m:ModuleV2 {id: r.module_id})
WITH r, s, m, EXISTS( (s)-[:HAS_PART]->(:SolutionV2) ) AS hasChildren
WHERE NOT (s.type = 'Hauptprozess' AND hasChildren)
MERGE (s)-[u:USES_MODULE]->(m)
SET u.dataset = 'equipment_solution_v2',
    u.qty = CASE WHEN r.qty IS NULL OR r.qty = '' THEN 1 ELSE toInteger(r.qty) END,
    u.role = CASE WHEN r.role IS NULL OR r.role = '' THEN NULL ELSE r.role END;


