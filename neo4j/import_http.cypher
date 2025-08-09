// Import from public GitHub raw URLs (no server file access required)
// Branch: feature/add-equipment-categories
// Repo: https://github.com/rishabh1815769/dehn-equipment-challenge

// Base: https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/

// Load reference nodes
USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/categories.csv' AS row
MERGE (:Category {name: row.name});

USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/manufacturers.csv' AS row
MERGE (:Manufacturer {name: row.name});

USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/properties.csv' AS row
MERGE (:Property {name: row.name});

// Components
USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/components.csv' AS row
MERGE (c:Component {id: row.id})
SET c.type = row.type,
    c.component_names = row.component_names;

// Relationships: MADE_BY
USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/component_manufacturer.csv' AS row
MATCH (c:Component {id: row.component_id})
MATCH (m:Manufacturer {name: row.manufacturer_name})
MERGE (c)-[:MADE_BY]->(m);

// Relationships: IN_CATEGORY
USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/component_category.csv' AS row
MATCH (c:Component {id: row.component_id})
MATCH (cat:Category {name: row.category_name})
MERGE (c)-[:IN_CATEGORY]->(cat);

// Relationships: HAS_PROPERTY with values
USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/component_properties.csv' AS row
MATCH (c:Component {id: row.component_id})
MERGE (p:Property {name: row.property_name})
MERGE (c)-[r:HAS_PROPERTY]->(p)
SET r.unit = CASE row.unit WHEN '' THEN NULL ELSE row.unit END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN NULL ELSE toFloat(row.numeric_value) END,
    r.text_value = CASE row.text_value WHEN '' THEN NULL ELSE row.text_value END,
    r.source = row.source;


