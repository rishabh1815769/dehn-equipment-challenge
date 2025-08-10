// Import from public GitHub raw URLs (no server file access required)
// Branch: feature/add-equipment-categories
// Repo: https://github.com/rishabh1815769/dehn-equipment-challenge

// Base: https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/

// Load reference nodes
CALL {
  LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/categories.csv' AS row
  MERGE (:Category {name: row.name});
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/manufacturers.csv' AS row
  MERGE (:Manufacturer {name: row.name});
} IN TRANSACTIONS OF 1000 ROWS;

CALL {
  LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/properties.csv' AS row
  MERGE (:Property {name: row.name});
} IN TRANSACTIONS OF 1000 ROWS;

// Components
CALL {
  LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/components.csv' AS row
  MERGE (c:Component {id: row.id})
  SET c.type = row.type,
      c.component_names = row.component_names;
} IN TRANSACTIONS OF 1000 ROWS;

// Relationships: MADE_BY
CALL {
  LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/component_manufacturer.csv' AS row
  MATCH (c:Component {id: row.component_id})
  MATCH (m:Manufacturer {name: row.manufacturer_name})
  MERGE (c)-[:MADE_BY]->(m);
} IN TRANSACTIONS OF 1000 ROWS;

// Relationships: IN_CATEGORY
CALL {
  LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/component_category.csv' AS row
  MATCH (c:Component {id: row.component_id})
  MATCH (cat:Category {name: row.category_name})
  MERGE (c)-[:IN_CATEGORY]->(cat);
} IN TRANSACTIONS OF 1000 ROWS;

// Relationships: HAS_PROPERTY with values
CALL {
  LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/rishabh1815769/dehn-equipment-challenge/feature/add-equipment-categories/staging/component_properties.csv' AS row
  MATCH (c:Component {id: row.component_id})
  MERGE (p:Property {name: row.property_name})
  MERGE (c)-[r:HAS_PROPERTY]->(p)
  SET r.unit = CASE row.unit WHEN '' THEN NULL ELSE row.unit END,
      r.numeric_value = CASE row.numeric_value WHEN '' THEN NULL ELSE toFloat(row.numeric_value) END,
      r.text_value = CASE row.text_value WHEN '' THEN NULL ELSE row.text_value END,
      r.source = row.source;
} IN TRANSACTIONS OF 1000 ROWS;


