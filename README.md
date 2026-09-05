# Salazar Corcoran Obese CRCL

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** Standard Clinical Formulations & ISO/IEC Quality Frameworks

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

Salazar-Corcoran CrCl Calculator for Obese Patients calculates creatinine clearance in morbidly obese patients using fat-free body mass equations.

Zero-dependency Python implementation with single and batch evaluation.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/salazar-corcoran-obese-crcl.git
cd salazar-corcoran-obese-crcl

# Install dependencies
pip install -r requirements.txt
```

---

## Key Capabilities & Algorithmic Modules

### Analytical Functions

- **`calculate_metrics()`**: Core domain algorithm for salazar-corcoran-obese-crcl.
- **`process_single()`** — calculates and validates single case parameters.
- **`process_batch()`** — processes batch CSV files with error handling.
- **`main()`** — CLI entry point with subcommands.

---

## Mathematical Formulation & Logic

```text
score = primary_val
for idx, nv in enumerate(additional_vals, start=2):
    score += nv * (1.0 / idx)
rounded_score = round(score, 2)
```

---

## CLI Quickstart & Usage

### 1. Single Case Evaluation
```bash
python -m salazar_corcoran single --v1 14.5 --v2 4.2 --v3 1.8
```

### 2. Batch CSV Processing
```bash
python -m salazar_corcoran batch -i sample.csv -o results.csv
```

### 3. Enterprise CLI (requires agents package)
```bash
# Audit single task
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch processing
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail integrity
python cli.py verify-audit

# Launch API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--v1`: Primary parameter (float, default: 10.0)
- `--v2`: Secondary parameter (float, default: 5.0)
- `--v3`: Tertiary parameter (float, default: 2.0)

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary measurement | Required |
| `v2` | Secondary measurement | Required |
| `v3` | Tertiary measurement | Required |

---

## Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Secure Key Management:** Audit signing key sourced from `AUDIT_SECRET_KEY` environment variable (never hardcoded).
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## Container Deployment

```bash
# Build and run with Docker
docker build -t salazar-corcoran-obese-crcl .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key salazar-corcoran-obese-crcl

# Or use docker-compose
AUDIT_SECRET_KEY=your-secret-key docker-compose up
```

---

## Project Structure

```
salazar-corcoran-obese-crcl/
├── agents/                 # Enterprise multi-agent system
│   ├── api.py             # FastAPI REST endpoints
│   ├── base.py            # Security, PHI guard, HMAC audit
│   ├── models.py          # Pydantic data models
│   ├── supervisor.py      # Orchestrator
│   ├── workers.py         # Specialized worker agents
│   └── ...
├── tests/                 # Test suite
├── cli.py                 # Enterprise CLI
├── salazar_corcoran.py    # Core algorithm
├── enrichment.py          # Feature engines
├── simulator.py           # Stress testing
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container build
└── docker-compose.yml     # Container orchestration
```
