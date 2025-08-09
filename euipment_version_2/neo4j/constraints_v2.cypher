// Constraints for isolated V2 dataset within single DB

CREATE CONSTRAINT solution_v2_id IF NOT EXISTS
FOR (s:SolutionV2)
REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT module_v2_id IF NOT EXISTS
FOR (m:ModuleV2)
REQUIRE m.id IS UNIQUE;


