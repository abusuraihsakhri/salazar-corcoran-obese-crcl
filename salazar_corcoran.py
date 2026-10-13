#!/usr/bin/env python3
"""Salazar–Corcoran (1988) estimated creatinine clearance for obese adults.

Inputs: age in years, actual weight in kg, height in metres, serum creatinine
in mg/dL, and sex-specific equation coefficient (male or female). The output
is estimated CrCl in mL/min, not a measured clearance or normalized eGFR.
"""

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

FIELDS = ("sex", "age_years", "weight_kg", "height_m", "serum_creatinine_mg_dl")
RESULT_FIELD = "creatinine_clearance_ml_min"


def _positive_finite(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a positive finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive finite number") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return number


def calculate_creatinine_clearance(*, sex: str, age_years: float,
                                   weight_kg: float, height_m: float,
                                   serum_creatinine_mg_dl: float) -> float:
    """Return the unrounded Salazar–Corcoran CrCl estimate in mL/min.

    The adult-specific equation assumes steady-state creatinine. It is not a
    substitute for measured clearance or an individualized dosing assessment.
    """
    if not isinstance(sex, str) or sex.strip().lower() not in {"male", "female"}:
        raise ValueError("sex must be 'male' or 'female' (equation coefficient)")
    sex = sex.strip().lower()
    age = _positive_finite(age_years, "age_years")
    weight = _positive_finite(weight_kg, "weight_kg")
    height = _positive_finite(height_m, "height_m")
    creatinine = _positive_finite(serum_creatinine_mg_dl, "serum_creatinine_mg_dl")
    if age < 18:
        raise ValueError("The equation is intended for adults aged 18 years or older")
    if sex == "male":
        if age >= 137:
            raise ValueError("age_years must be less than 137 for the male equation")
        return ((137 - age) * (0.285 * weight + 12.1 * height**2)) / (51 * creatinine)
    if age >= 146:
        raise ValueError("age_years must be less than 146 for the female equation")
    return ((146 - age) * (0.287 * weight + 9.74 * height**2)) / (60 * creatinine)


def calculate_metrics(**kwargs: Any) -> dict[str, Any]:
    """Evaluate the named clinical inputs; reject missing/unknown inputs."""
    missing = [name for name in FIELDS if name not in kwargs]
    unknown = [name for name in kwargs if name not in FIELDS]
    if missing or unknown:
        raise ValueError(f"Expected fields {', '.join(FIELDS)}; missing={missing}, unknown={unknown}")
    crcl = calculate_creatinine_clearance(**kwargs)
    return {
        "tool": "salazar-corcoran-obese-crcl",
        RESULT_FIELD: round(crcl, 2),
        "unit": "mL/min",
        "equation": "Salazar-Corcoran (1988)",
    }


def _spreadsheet_safe(value: Any) -> Any:
    """Prevent formula execution when exported CSV is opened in a spreadsheet."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def process_batch(input_csv: str, output_csv: str) -> int:
    """Validate entire CSV before writing output; preserve non-clinical columns."""
    input_path = Path(input_csv)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input CSV file not found: {input_csv}")
    with input_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        if not columns:
            raise ValueError("Input CSV file is empty or has no headers")
        if len(columns) != len(set(columns)) or any(not c for c in columns):
            raise ValueError("CSV contains duplicate or empty column headers")
        missing = [field for field in FIELDS if field not in columns]
        if missing:
            raise ValueError(f"Missing required CSV columns: {', '.join(missing)}")
        if RESULT_FIELD in columns:
            raise ValueError(f"Input CSV already contains output column: {RESULT_FIELD}")
        output_rows = []
        for line_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV row {line_number}: inconsistent column count")
            try:
                result = calculate_metrics(**{field: row[field] for field in FIELDS})
            except ValueError as exc:
                raise ValueError(f"CSV row {line_number}: {exc}") from exc
            safe_row = {key: _spreadsheet_safe(value) for key, value in row.items()}
            safe_row[RESULT_FIELD] = result[RESULT_FIELD]
            output_rows.append(safe_row)

    output_path = Path(output_csv)
    if not output_path.parent.is_dir():
        raise FileNotFoundError(f"Output directory does not exist: {output_path.parent}")
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Output CSV must differ from input CSV")
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[*columns, RESULT_FIELD])
        writer.writeheader()
        writer.writerows(output_rows)
    return len(output_rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Salazar–Corcoran CrCl estimate for obese adults")
    subparsers = parser.add_subparsers(dest="command", required=True)
    single = subparsers.add_parser("single", help="Estimate one adult's CrCl")
    single.add_argument("--sex", required=True, choices=["male", "female"])
    single.add_argument("--age-years", type=float, required=True)
    single.add_argument("--weight-kg", type=float, required=True)
    single.add_argument("--height-m", type=float, required=True)
    single.add_argument("--serum-creatinine-mg-dl", type=float, required=True)
    batch = subparsers.add_parser("batch", help="Validate and calculate CSV rows")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            values = vars(args).copy()
            values.pop("command")
            print(json.dumps(calculate_metrics(**values), indent=2))
        else:
            count = process_batch(args.input, args.output)
            print(f"Processed {count} records -> {args.output}")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
