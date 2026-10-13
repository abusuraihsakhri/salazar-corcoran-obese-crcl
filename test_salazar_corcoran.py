"""Clinical reference values and invalid-input tests for Salazar–Corcoran."""
import csv
import pytest
from salazar_corcoran import calculate_creatinine_clearance, calculate_metrics, process_batch

MALE = dict(sex="male", age_years=45, weight_kg=120, height_m=1.75, serum_creatinine_mg_dl=1.2)
FEMALE = dict(sex="female", age_years=55, weight_kg=110, height_m=1.65, serum_creatinine_mg_dl=1.4)


def test_reference_male():
    assert calculate_creatinine_clearance(**MALE) == pytest.approx(107.1172385620915)


def test_reference_female():
    assert calculate_creatinine_clearance(**FEMALE) == pytest.approx(62.92774583333333)


def test_rounding():
    assert calculate_metrics(**MALE)["creatinine_clearance_ml_min"] == 107.12
    assert calculate_metrics(**FEMALE)["creatinine_clearance_ml_min"] == 62.93


@pytest.mark.parametrize("override", [
    {"serum_creatinine_mg_dl": 0}, {"serum_creatinine_mg_dl": float("nan")},
    {"age_years": 17}, {"weight_kg": -5}, {"height_m": float("inf")},
    {"sex": "other"}, {"age_years": 137}, {"weight_kg": True},
])
def test_invalid_inputs(override):
    with pytest.raises(ValueError):
        calculate_creatinine_clearance(**(MALE | override))


def test_no_generic_score():
    with pytest.raises(ValueError, match="Expected fields"):
        calculate_metrics(v1=10, v2=5)


def test_csv(tmp_path):
    input_file, output_file = tmp_path / "in.csv", tmp_path / "out.csv"
    input_file.write_text(
        "case_id,sex,age_years,weight_kg,height_m,serum_creatinine_mg_dl\n"
        "PT-001,male,45,120,1.75,1.2\nPT-002,female,55,110,1.65,1.4\n",
        encoding="utf-8")
    assert process_batch(str(input_file), str(output_file)) == 2
    with output_file.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert [row["creatinine_clearance_ml_min"] for row in rows] == ["107.12", "62.93"]


def test_csv_atomic_failure(tmp_path):
    source, target = tmp_path / "in.csv", tmp_path / "out.csv"
    source.write_text("sex,age_years,weight_kg,height_m,serum_creatinine_mg_dl\n"
                      "male,45,120,1.75,1.2\nfemale,55,110,1.65,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="row 3"):
        process_batch(str(source), str(target))
    assert not target.exists()


def test_csv_formula_injection(tmp_path):
    source, target = tmp_path / "in.csv", tmp_path / "out.csv"
    source.write_text("case_id,sex,age_years,weight_kg,height_m,serum_creatinine_mg_dl\n"
                      '"=1+1",male,45,120,1.75,1.2\n', encoding="utf-8")
    process_batch(str(source), str(target))
    assert "'=1+1" in target.read_text(encoding="utf-8")
