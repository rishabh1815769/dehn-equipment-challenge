// Assumes all staging CSVs are copied into Neo4j's import directory
// Files expected: categories.csv, manufacturers.csv, properties.csv,
// components.csv, component_manufacturer.csv, component_category.csv,
// component_properties.csv

// Load reference nodes
USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'file:///categories.csv' AS row
MERGE (:Category {name: row.name});

USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'file:///manufacturers.csv' AS row
MERGE (:Manufacturer {name: row.name});

USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'file:///properties.csv' AS row
MERGE (:Property {name: row.name});

// Components
USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'file:///components.csv' AS row
MERGE (c:Component {id: row.id})
SET c.type = row.type,
    c.component_names = row.component_names;

// Relationships: MADE_BY
USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'file:///component_manufacturer.csv' AS row
MATCH (c:Component {id: row.component_id})
MATCH (m:Manufacturer {name: row.manufacturer_name})
MERGE (c)-[:MADE_BY]->(m);

// Relationships: IN_CATEGORY
USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'file:///component_category.csv' AS row
MATCH (c:Component {id: row.component_id})
MATCH (cat:Category {name: row.category_name})
MERGE (c)-[:IN_CATEGORY]->(cat);

// Relationships: HAS_PROPERTY with values
USING PERIODIC COMMIT 1000
LOAD CSV WITH HEADERS FROM 'file:///component_properties.csv' AS row
MATCH (c:Component {id: row.component_id})
MERGE (p:Property {name: row.property_name})
MERGE (c)-[r:HAS_PROPERTY]->(p)
SET r.unit = CASE row.unit WHEN '' THEN NULL ELSE row.unit END,
    r.numeric_value = CASE row.numeric_value WHEN '' THEN NULL ELSE toFloat(row.numeric_value) END,
    r.text_value = CASE row.text_value WHEN '' THEN NULL ELSE row.text_value END,
    r.source = row.source;


