#!/usr/bin/env python3
import json
import sys
import os
import uuid
import copy
from typing import Dict, Any

def flatten(prefix: str, data: Dict, output: Dict):
    """
    Aplati récursivement un dictionnaire.
    Exemple : {"a": {"b": 1}} devient {"prefix.a.b": 1}
    """
    if not isinstance(data, dict):
        return
    for key, value in data.items():
        new_key = f"{prefix}.{key}"
        if isinstance(value, dict):
            flatten(new_key, value, output)
        else:
            output[new_key] = value

def ensure_dict(obj):
    return obj if isinstance(obj, dict) else {}

def split_and_write(input_file: str, output_file: str):
    """
    - Produit 1 document parent vuln_report (intact)
    - Produit N documents findings (aplatis)
      - Tous les champs du finding sont à la racine et préfixés :
         - 'vulnerability.*' pour champs venant du vuln element
         - 'metadata.*' pour métadonnées du parent (si présentes)
         - 'service.*' et 'tool.*' (si présents au parent)
      - Ajoute report_id sur parent ET sur chaque finding (report_id)
    """
    try:
        print(f" Lecture du rapport normalisé: {input_file}")
        with open(input_file, "r", encoding="utf-8") as f:
            report_data = json.load(f)
    except Exception as e:
        print(f"Erreur de lecture/parsing du fichier {input_file}: {e}")
        sys.exit(1)

    # --- 1) assigner report_id (ne pas muter report_data initial)
    report_id = str(uuid.uuid4())
    report_data_with_id = copy.deepcopy(report_data)
    report_data_with_id["report_id"] = report_id

    vulnerabilities = report_data_with_id.get("vulnerabilities", [])
    output_documents = []

    # --- 2) préparer parent doc (intact)
    parent_doc = copy.deepcopy(report_data_with_id)
    parent_doc["doc_type"] = "vulnerability_report"

    # --- 3) creation des findings aplatis
    if isinstance(vulnerabilities, list) and len(vulnerabilities) > 0:
        print(f" Génération de {len(vulnerabilities)} findings...")
        # pre-extract some parent-level metadata to inject into each finding:
        parent_metadata = ensure_dict(report_data_with_id.get("metadata", {}))
        parent_service = ensure_dict(report_data_with_id.get("service", {}))
        parent_tool = ensure_dict(report_data_with_id.get("tool", {}))
        # also include build, git, pipeline top-level if exist
        parent_build = ensure_dict(report_data_with_id.get("build", {}))
        parent_git = ensure_dict(report_data_with_id.get("git", {}))
        parent_pipeline = ensure_dict(report_data_with_id.get("pipeline", {}))

        for vuln_item in vulnerabilities:
            vuln_copy = copy.deepcopy(vuln_item)  # safety
            child_doc = {
                "doc_type": "vulnerability_finding",
                "report_id": report_id
            }

            # flatten vuln fields under vulnerability.*
            if isinstance(vuln_copy, dict):
                flatten("vulnerability", vuln_copy, child_doc)

            # ensure unified is also flattened under vulnerability.unified.* (no duplication)
            unified = vuln_copy.get("unified") if isinstance(vuln_copy, dict) else None
            if isinstance(unified, dict):
                flatten("vulnerability.unified", unified, child_doc)

            # Inject parent metadata into the finding under 'metadata.*'
            if parent_metadata:
                flatten("metadata", parent_metadata, child_doc)

            # also inject parent service/tool/build/git/pipeline in explicit fields
            if parent_service:
                flatten("service", parent_service, child_doc)
            if parent_tool:
                flatten("tool", parent_tool, child_doc)
            if parent_build:
                flatten("build", parent_build, child_doc)
            if parent_git:
                flatten("git", parent_git, child_doc)
            if parent_pipeline:
                flatten("pipeline", parent_pipeline, child_doc)

            # keep the parent report_id in child (already set)
            child_doc["report_id"] = report_id

            output_documents.append(child_doc)
    else:
        print(" Aucune vulnérabilité trouvée dans ce rapport.")

    # --- 4) append parent doc at the end (intact)
    output_documents.append(parent_doc)

    # --- 5) write NDJSON atomically
    temp_output_file = output_file + ".tmp"
    try:
        print(f" Écriture de {len(output_documents)} documents dans {temp_output_file}...")
        with open(temp_output_file, "w", encoding="utf-8") as f:
            for doc in output_documents:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")

        if os.path.exists(output_file):
            os.remove(output_file)
        os.rename(temp_output_file, output_file)
        print(f"Succès. Fichier généré : {output_file}")
    except Exception as e:
        print(f"Erreur d'écriture : {e}")
        if os.path.exists(temp_output_file):
            os.remove(temp_output_file)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 split_reports.py <input_json> <output_ndjson>")
        sys.exit(1)
    split_and_write(sys.argv[1], sys.argv[2])
