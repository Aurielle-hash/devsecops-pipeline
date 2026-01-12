
# 🐍 Scripts Python

Scripts de normalisation des rapports de sécurité.

## normalize_reports.py

**Rôle** : Convertir rapports Snyk/Trivy/SonarQube vers Elastic Common Schema (ECS).

**Inputs** :
- `sonarqube-backend.json`
- `snyk-backend.json`
- `trivy-backend.json`

**Output** :
- `report.json` (format ECS unifié)

**Fonctionnalités** :
- Normalisation champs → ECS
- Calcul MTTD-CI
- Enrichissement métadonnées Git
- Gestion des états (open/closed)

## split_reports.py

**Rôle** : Découper rapport unifié en documents Parent/Enfant.

**Input** : `report.json`

**Output** : `report.ndjson` (NDJSON multi-docs)

**Format** :


```json
{"doc_type": "vulnerability_report", "vulnerabilities": [...]}
{"doc_type": "vulnerability_finding", "vulnerability_id": "CVE-..."}
{"doc_type": "vulnerability_finding", "vulnerability_id": "SNYK-..."}
```
## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python normalize_reports.py /shared/build-123
python split_reports.py /shared/build-123/report.json
```
