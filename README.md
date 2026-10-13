# Salazar–Corcoran Creatinine Clearance Calculator

Reference implementation of the 1988 Salazar–Corcoran equations for estimating creatinine clearance (CrCl) in obese adults. Provides a standalone browser calculator, Python API/CLI, and batch CSV processing.

**Clinical limitation:** The result is an estimate, not measured clearance or an individualized medication-dosing recommendation. The equation assumes stable serum creatinine and is not intended for children. Estimates may be unreliable in critical illness or rapidly changing renal function.

## Browser calculator

The static application is in [web/index.html](web/index.html). It provides:

- Male/female equation selection and explicit units (years, kg, m, mg/dL).
- Estimated CrCl in **mL/min** (not indexed to 1.73 m²).
- Local CSV upload, calculation, validation, and results download.
- No external calculation backend, account, analytics, cookies, or upload.

The GitHub Pages publication workflow is configured in this repository. A live URL will be added below the title only after deployment and browser access are verified.

To use it locally, run:

    python -m http.server 8000 -d web

Then open http://localhost:8000/ in a modern browser.

**CSV schema:** required headers are sex, age_years, weight_kg, height_m, and serum_creatinine_mg_dl. Additional columns are preserved. See [sample.csv](sample.csv). Browser batch limit: 2 MiB and 2,000 data rows. Do not use real identifying patient information on public devices.

## Clinical formula

Inputs are actual body weight in kg, height in metres, age in years, and serum creatinine (SCr) in mg/dL.

For men:

    CrCl = (137 - age) × (0.285 × weight + 12.1 × height²) / (51 × SCr)

For women:

    CrCl = (146 - age) × (0.287 × weight + 9.74 × height²) / (60 × SCr)

Output: **mL/min**. Calculations retain full precision until presentation, then round to two decimal places.

Examples: male aged 45 years, 120 kg, 1.75 m, SCr 1.2 mg/dL → **107.12 mL/min**. Female aged 55 years, 110 kg, 1.65 m, SCr 1.4 mg/dL → **62.93 mL/min**.

**Primary reference:** Salazar DE, Corcoran GB. Predicting creatinine clearance and renal drug clearance in obese patients from estimated fat-free body mass. *Am J Med*. 1988;84(6):1053–1060. [PMID: 3376975](https://pubmed.ncbi.nlm.nih.gov/3376975/); DOI: 10.1016/0002-9343(88)90310-5.

A study of obese critically ill patients reported clinically unacceptable agreement between estimates and measured 24-hour urinary clearance. See [PMID: 8602383](https://pubmed.ncbi.nlm.nih.gov/8602383/). For consequential clinical decisions, consult current guidance and consider direct measurement when appropriate.

## Python usage

Requires Python 3.10+. The **core formula uses only the standard library**. Optional FastAPI/legacy components and tests depend on [requirements.txt](requirements.txt).

    python -m pip install -r requirements.txt
    python -m salazar_corcoran single --sex male --age-years 45 --weight-kg 120 --height-m 1.75 --serum-creatinine-mg-dl 1.2
    python -m salazar_corcoran batch -i sample.csv -o results.csv

Unrounded programmatic result:

    from salazar_corcoran import calculate_creatinine_clearance
    crcl = calculate_creatinine_clearance(sex="female", age_years=55, weight_kg=110, height_m=1.65, serum_creatinine_mg_dl=1.4)

Missing, nonfinite, and invalid inputs raise descriptive errors. CSV batches validate all rows before writing output. Potential spreadsheet formulas in exported text cells are escaped.

## Optional API and legacy components

Start the server with:

    python cli.py serve --host 127.0.0.1 --port 8000

- POST /api/crcl accepts the five clinical inputs, returning the estimate.
- GET /health and GET /metrics expose JSON health/counter information.
- Legacy /api/audit, /api/chat, and /api/audit/logs are **generic prototype utilities**, not Salazar–Corcoran clinical decision rules. Mock chat does not perform clinical verification or inference.
- **No authentication is provided**. Do not expose the server on untrusted networks or send identifying patient data. Legacy regex matching is not reliable de-identification or a HIPAA compliance control.
- The in-memory audit metadata is HMAC-SHA256-signed; persistent production-grade audit logging is not implemented.

Container example: build with Docker using [Dockerfile](Dockerfile), then deploy only behind appropriate network controls.

## Testing

    python -m pytest -q
    cd web && npm test && node --check app.js

Python tests cover reference values, input validation, CSV processing, and legacy prototype regression. Node.js 22 tests exercise the browser computational module. GitHub Actions runs Python 3.10–3.12 and Node.js.

## Privacy and compatibility

The browser app calculates locally in memory; uploaded CSV is not sent to a server. Modern browsers supporting ECMAScript modules, File/Blob APIs, and local downloads are required. GitHub Pages serves JavaScript directly; **Python does not run in the browser**, and Pyodide is unnecessary here.

## License

MIT — see [LICENSE](LICENSE).
