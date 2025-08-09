#!/usr/bin/env python3
"""
Prepare staging CSVs for Neo4j import from building_blocks_cleaned.csv.

This script reads the source CSV and produces the following files in ./staging:
  - categories.csv: name
  - manufacturers.csv: name
  - properties.csv: name
  - components.csv: id,type,component_names
  - component_manufacturer.csv: component_id,manufacturer_name
  - component_category.csv: component_id,category_name
  - component_properties.csv: component_id,property_name,unit,numeric_value,text_value,source

Design notes:
- Property node names remain EXACTLY as in the CSV (unchanged), per user requirements.
- Units are parsed from square brackets in the property name and stored on the relationship.
- Values are split into numeric_value (float when parseable) or text_value (string).
- Empty strings and '-' placeholders are treated as NULL and omitted where appropriate.
- The pipeline is deterministic and idempotent: rerunning regenerates the same staging files.

Usage:
  python3 scripts/prepare_staging.py [--input path/to/building_blocks_cleaned.csv] [--out staging]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


LOGGER = logging.getLogger("prepare_staging")


PROPERTY_COLUMNS: Tuple[str, str, str] = ("property_1", "property_2", "property_3")
VALUE_COLUMNS: Tuple[str, str, str] = ("value_1", "value_2", "value_3")


@dataclass(frozen=True)
class Component:
    component_id: str
    type: str
    component_names: str


def configure_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def read_rows(input_path: Path) -> Iterable[Dict[str, str]]:
    try:
        with input_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row
    except FileNotFoundError:
        LOGGER.exception("Input CSV not found: %s", input_path)
        raise
    except Exception:
        LOGGER.exception("Failed to read CSV: %s", input_path)
        raise


def is_nullish(value: Optional[str]) -> bool:
    if value is None:
        return True
    v = value.strip()
    return v == "" or v == "-"


_UNIT_REGEX = re.compile(r"\[(.*?)\]")


def parse_unit_from_property(property_name: str) -> str:
    """Extract unit substring inside square brackets from the property name.

    Example: "Load capacity [kg]" -> "kg". Returns empty string if no unit.
    DOES NOT modify the property name; caller must keep it unchanged elsewhere.
    """
    match = _UNIT_REGEX.search(property_name)
    return match.group(1).strip() if match else ""


def parse_float(value: str) -> Optional[float]:
    """Parse a numeric string to float; return None if not a clean number.

    Accepts dot decimal separator only. Strings containing spaces, ranges ("1-2"),
    slashes ("7200/7250"), or letters are treated as non-numeric.
    """
    v = value.strip()
    # Reject obviously non-numeric patterns quickly
    if not v:
        return None
    if any(sym in v for sym in [" ", "/", "-", ",", ";", ":", "(", ")", "[", "]"]):
        # If it is a negative number like -5, allow a leading dash but not ranges "1-2"
        if v.startswith("-") and v[1:].replace(".", "").isdigit():
            try:
                return float(v)
            except ValueError:
                return None
        return None
    # Only digits and at most one dot
    try:
        return float(v)
    except ValueError:
        return None


def generate_component_id(manufacturer: str, type_name: str, component_names: str) -> str:
    """Stable identifier derived from key fields using SHA-1.

    We avoid exposing raw hashes in the graph name space, but a hex digest is fine
    as an identifier property. Inputs are trimmed and lower-cased for stability.
    """
    base = f"{manufacturer.strip().lower()}|{type_name.strip().lower()}|{component_names.strip().lower()}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, header: List[str], rows: Iterable[Iterable[object]]) -> None:
    try:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)
    except Exception:
        LOGGER.exception("Failed to write CSV: %s", path)
        raise


def build_staging(input_path: Path, out_dir: Path) -> None:
    LOGGER.info("Building staging from: %s", input_path)

    categories: Set[str] = set()
    manufacturers: Set[str] = set()
    properties: Set[str] = set()
    components: Dict[str, Component] = {}

    component_to_manufacturer: List[Tuple[str, str]] = []
    component_to_category: List[Tuple[str, str]] = []
    component_properties: List[Tuple[str, str, str, Optional[float], str, str]] = []
    # tuple: (component_id, property_name, unit, numeric_value, text_value, source)

    for idx, row in enumerate(read_rows(input_path), start=2):  # header is line 1
        try:
            category = (row.get("component_category") or "").strip()
            manufacturer = (row.get("manufacturer") or "").strip()
            type_name = (row.get("type") or "").strip()
            component_names = (row.get("component_names") or "").strip()

            if is_nullish(category) and is_nullish(manufacturer) and is_nullish(type_name) and is_nullish(component_names):
                LOGGER.debug("Skipping empty row at line %d", idx)
                continue

            comp_id = generate_component_id(manufacturer, type_name, component_names)
            if comp_id not in components:
                components[comp_id] = Component(
                    component_id=comp_id,
                    type=type_name,
                    component_names=component_names,
                )

            if not is_nullish(category):
                categories.add(category)
                component_to_category.append((comp_id, category))

            if not is_nullish(manufacturer):
                manufacturers.add(manufacturer)
                component_to_manufacturer.append((comp_id, manufacturer))

            # Extract up to three property/value pairs
            for p_col, v_col in zip(PROPERTY_COLUMNS, VALUE_COLUMNS):
                p_raw = row.get(p_col)
                v_raw = row.get(v_col)
                if is_nullish(p_raw) or is_nullish(v_raw):
                    continue
                prop_name = p_raw.strip()
                properties.add(prop_name)
                unit = parse_unit_from_property(prop_name)
                numeric_value = parse_float(v_raw)
                text_value = "" if numeric_value is not None else v_raw.strip()
                source = f"{input_path.name}:{idx}:{p_col}/{v_col}"
                component_properties.append(
                    (comp_id, prop_name, unit, numeric_value, text_value, source)
                )
        except Exception:
            LOGGER.exception("Error processing row at line %d", idx)
            raise

    LOGGER.info("Counts -> components=%d, categories=%d, manufacturers=%d, properties=%d, rel_props=%d",
                len(components), len(categories), len(manufacturers), len(properties), len(component_properties))

    ensure_dir(out_dir)

    # Write reference files
    write_csv(out_dir / "categories.csv", ["name"], sorted((c,) for c in categories))
    write_csv(out_dir / "manufacturers.csv", ["name"], sorted((m,) for m in manufacturers))
    write_csv(out_dir / "properties.csv", ["name"], sorted((p,) for p in properties))

    # Write components
    write_csv(
        out_dir / "components.csv",
        ["id", "type", "component_names"],
        ((c.component_id, c.type, c.component_names) for c in components.values()),
    )

    # Write relationships
    write_csv(
        out_dir / "component_manufacturer.csv",
        ["component_id", "manufacturer_name"],
        component_to_manufacturer,
    )
    write_csv(
        out_dir / "component_category.csv",
        ["component_id", "category_name"],
        component_to_category,
    )
    write_csv(
        out_dir / "component_properties.csv",
        ["component_id", "property_name", "unit", "numeric_value", "text_value", "source"],
        (
            (
                comp_id,
                prop_name,
                unit,
                ("" if num is None else f"{num}"),
                text_value,
                source,
            )
            for (comp_id, prop_name, unit, num, text_value, source) in component_properties
        ),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare staging CSVs for Neo4j import")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("building_blocks_cleaned.csv"),
        help="Path to source CSV (default: building_blocks_cleaned.csv)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("staging"),
        help="Output directory for staging CSVs (default: staging)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.debug)
    try:
        build_staging(args.input, args.out)
        LOGGER.info("Staging files written to: %s", args.out.resolve())
    except Exception as exc:
        LOGGER.exception("Staging preparation failed: %s", exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()


