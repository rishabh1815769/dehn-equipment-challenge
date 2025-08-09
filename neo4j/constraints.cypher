// Constraints and indexes for the DEHN equipment graph

// Unique identifiers
CREATE CONSTRAINT component_id_unique IF NOT EXISTS
FOR (c:Component)
REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT category_name_unique IF NOT EXISTS
FOR (c:Category)
REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT manufacturer_name_unique IF NOT EXISTS
FOR (m:Manufacturer)
REQUIRE m.name IS UNIQUE;

CREATE CONSTRAINT property_name_unique IF NOT EXISTS
FOR (p:Property)
REQUIRE p.name IS UNIQUE;

// Optional: Full-text index for quick search on components
CREATE FULLTEXT INDEX component_search IF NOT EXISTS
FOR (n:Component) ON EACH [n.type, n.component_names];


