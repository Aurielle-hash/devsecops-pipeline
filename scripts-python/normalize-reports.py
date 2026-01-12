"""
Script de normalisation des rapports de sécurité
Version: 3.0 (MTTD/MTTR automatisés + Recommandations)
Date: 2025-01-21

Modifications v3.0:
- Calcul MTTD sur 7 jours glissants par outil
- Extraction recommandations de mitigation
- Écriture atomique (.tmp → rename)
- Format metrics.mttd.{tool}.{1d-7d}
- Format metrics.mttr.{tool}

Usage:
    python3 normalize-reports.py <input_file> <output_file> <tool> <metadata_json>
"""

import json
import sys
import os
from typing import Dict, Any, List, Optional
import traceback
from datetime import datetime, timedelta, timezone
import statistics


class ReportNormalizer:
    """Normalise les rapports de sécurité pour Elasticsearch avec MTTD/MTTR"""

    def __init__(self, tool: str, metadata: Dict[str, Any]):
        self.tool = tool.lower()
        self.metadata = metadata
        # self.scan_end_time = metadata.get('scan_end_time')

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Point d'entrée principal de normalisation"""

        # Structure de base normalisée (PRÉSERVÉE)
        normalized = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "event": {
                "created": datetime.now(timezone.utc).isoformat(),
                "dataset": self.tool,
                "kind": "event",
                "category": ["vulnerability"],
                "type": ["info"],
                "module": "security_pipeline"
            },
            "metadata": {
                "tool": self.tool,
                "tool_version": self._extract_tool_version(raw_data),
                "service": self.metadata.get("service", "unknown"),
                "build_id": self.metadata.get("build_id", "unknown"),
                "scan_type": self.metadata.get("scan_type", "unknown"),
                "scan_start_time": self.metadata.get("scan_start_time", 0),
                "scan_end_time": self.metadata.get("scan_end_time", 0),
                "scan_duration_ms": self.metadata.get("scan_end_time") - self.metadata.get("scan_start_time"),
                "git": {
                    "commit": self.metadata.get("git_commit", ""),
                    "commit_time": self.metadata.get("code_introduction_time", 0),
                    "author": self.metadata.get("git_author", "DevTeam"),
                    "branch": self.metadata.get("git_branch", "main")
                },
                "pipeline": {
                    "source": "jenkins",
                    "environment": self.metadata.get("environment", "dev")
                }
            },
            "summary": {
                "total_vulnerabilities": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
                "severity_distribution": {}
            },
            "vulnerabilities": [],
            "metrics": {
                "mttd": {},
                "quality": {}
            }
        }

        # Normalisation spécifique par outil
        if self.tool == "snyk":
            normalized = self._normalize_snyk(raw_data, normalized)
        elif self.tool == "trivy":
            normalized = self._normalize_trivy(raw_data, normalized)
        elif self.tool == "sonarqube":
            normalized = self._normalize_sonarqube(raw_data, normalized)
        else:
            print(f"Outil non supporté: {self.tool}")
            normalized["raw_data"] = raw_data

        #NOUVEAU : Calcul MTTD
        normalized = self._calculate_mttd(normalized)

        #NOUVEAU : Initialiser MTTR (sera calculé par le watcher)
        normalized = self._initialize_mttr(normalized)

        return normalized

    def _normalize_snyk(self, data: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
        """Normalisation Snyk avec extraction recommandations et unification des références"""

        vulnerabilities = data.get("vulnerabilities", [])
        scan_end_time = normalized.get("@timestamp")

        for vuln in vulnerabilities:
            severity = vuln.get("severity", "unknown").lower()

            normalized["summary"]["total_vulnerabilities"] += 1
            if severity in normalized["summary"]:
                normalized["summary"][severity] += 1

            recommendation = self._extract_snyk_recommendation(vuln)

            # CORRECTION CRITIQUE : Unifier la structure de references
            refs_raw = vuln.get("references", [])
            refs = []

            if isinstance(refs_raw, list):
                for r in refs_raw:
                    if isinstance(r, dict):
                        # Convertir objet {"url": "...", "title": "..."} en chaîne
                        url = r.get("url", "")
                        if url and isinstance(url, str):
                            refs.append(url.strip())
                    elif isinstance(r, str) and r.strip():
                        # Déjà une chaîne
                        refs.append(r.strip())
            elif isinstance(refs_raw, str) and refs_raw.strip():
                refs = [refs_raw.strip()]

            # Dédupliquer et nettoyer
            refs = list(dict.fromkeys(refs))  # Supprimer les doublons tout en gardant l'ordre

            # --- Snyk-specific fields for unified ---
            has_fix = bool(vuln.get("fixedIn")) and len(vuln.get("fixedIn", [])) > 0
            fix_version = vuln.get("fixedIn", [None])[0] if has_fix else ""
            can_auto_upgrade = vuln.get("isUpgradable", False)
            exploit_maturity = vuln.get("exploitMaturity", "no-known-exploit").lower()
            exploit_exists = exploit_maturity in ['mature', 'proof-of-concept']

            pkg_name = vuln.get("packageName", "")
            pkg_version = vuln.get("version", "")
            package_full = f"{pkg_name}@{pkg_version}" if pkg_name and pkg_version else (pkg_name or 'unknown')

            is_sca = "maven" in self.metadata.get("scan_type", "").lower() or "npm" in self.metadata.get("scan_type", "").lower()
            vuln_type = "cve" if vuln.get("identifiers", {}).get("CVE") else ("sca" if is_sca else "code")

            # Nettoyage des CVE et CWE
            cve_ids = vuln.get("identifiers", {}).get("CVE", [])
            if isinstance(cve_ids, list):
                cve_ids = [str(c).strip() for c in cve_ids if c]
            else:
                cve_ids = []

            cwe_ids = vuln.get("identifiers", {}).get("CWE", [])
            if isinstance(cwe_ids, list):
                cwe_ids = [str(c).strip() for c in cwe_ids if c]
            else:
                cwe_ids = []

            normalized_vuln = {
                "id": vuln.get("id", ""),
                "title": vuln.get("title", ""),
                "severity": severity,
                "cvss_score": vuln.get("cvssScore", 0),
                "package": {
                    "name": pkg_name,
                    "version": pkg_version
                },
                "fixed_in": vuln.get("fixedIn", []),
                "is_upgradable": can_auto_upgrade,
                "is_patchable": vuln.get("isPatchable", False),
                "cve": cve_ids,
                "cwe": cwe_ids,
                "references": refs,  # ← LISTE DE CHAÎNES UNIFIÉE
                "publication_time": vuln.get("publicationTime", None),
                "disclosure_time": vuln.get("disclosureTime", None),
                "exploit_maturity": exploit_maturity,
                "mitigation_recommendation": recommendation
            }

            # INJECTION DU BLOC UNIFIED
            normalized_vuln['unified'] = self._create_unified_block(
                tool_id=vuln.get("id", f"snyk:unknown"),
                tool_type=vuln_type,
                severity=severity,
                score=vuln.get("cvssScore") or self._get_severity_score(severity),
                is_security_issue=True,
                is_vulnerability=True,
                category='security',
                is_fixable=has_fix,
                fix_version=fix_version,
                can_auto_upgrade=can_auto_upgrade,
                is_exploitable=exploit_exists,
                exploit_maturity=exploit_maturity,
                component=package_full,
                location=package_full,
                creation_time=vuln.get("publicationTime"),
                current_time=scan_end_time
            )

            normalized["vulnerabilities"].append(normalized_vuln)

        normalized["metadata"]["snyk"] = {
            "project_name": data.get("projectName", ""),
            "org": data.get("org", ""),
            "test_type": "sca" if "maven" in self.metadata.get("scan_type", "") else "code",
            "dependencies_analyzed": data.get("dependencyCount", 0)
        }

        normalized["summary"]["severity_distribution"] = {
            "critical": normalized["summary"]["critical"],
            "high": normalized["summary"]["high"],
            "medium": normalized["summary"]["medium"],
            "low": normalized["summary"]["low"]
        }

        return normalized

    def _normalize_trivy(self, data: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
        """Normalisation Trivy avec extraction recommandations et nettoyage des références"""

        results = data.get("Results", [])
        scan_end_time = normalized.get("@timestamp")

        for result in results:
            target = result.get("Target", "")
            vulns = result.get("Vulnerabilities") or []

            for vuln in vulns:
                severity = vuln.get("Severity", "UNKNOWN").lower()

                severity_map = {
                    "critical": "critical",
                    "high": "high",
                    "medium": "medium",
                    "low": "low",
                    "unknown": "info"
                }
                mapped_severity = severity_map.get(severity, "info")

                normalized["summary"]["total_vulnerabilities"] += 1
                if mapped_severity in normalized["summary"]:
                    normalized["summary"][mapped_severity] += 1

                recommendation = self._extract_trivy_recommendation(vuln)

                # CORRECTION CRITIQUE : Nettoyage robuste des références
                refs_raw = vuln.get("references") or vuln.get("References") or []

                # Assurer que refs est une liste de chaînes valides
                if isinstance(refs_raw, list):
                    refs = [str(r).strip() for r in refs_raw if r is not None and str(r).strip()]
                elif isinstance(refs_raw, str):
                    refs = [refs_raw.strip()] if refs_raw.strip() else []
                else:
                    refs = []

                # --- Trivy-specific fields for unified ---
                fixed_version = vuln.get("FixedVersion") or ""
                has_fix = bool(fixed_version)
                pkg_name = vuln.get("PkgName", "")
                pkg_version = vuln.get("InstalledVersion", "")
                package_full = f"{pkg_name}@{pkg_version}" if pkg_name and pkg_version else (pkg_name or 'unknown')

                vuln_id = vuln.get("VulnerabilityID", "")
                cve_list = [vuln_id] if vuln_id.startswith("CVE") else []
                vuln_type = "cve" if cve_list else "sca"

                # Nettoyage des CWE IDs
                cwe_ids = vuln.get("CweIDs") or vuln.get("cwe") or []
                if isinstance(cwe_ids, list):
                    cwe_ids = [str(c).strip() for c in cwe_ids if c is not None and str(c).strip()]
                else:
                    cwe_ids = []

                # Nettoyage des dates
                pub_time = vuln.get("PublishedDate") or vuln.get("publication_time") or None
                mod_time = vuln.get("LastModifiedDate") or vuln.get("last_modified_time") or None

                normalized_vuln = {
                    "id": vuln_id,
                    "title": vuln.get("Title", ""),
                    "severity": mapped_severity,
                    "cvss_score": self._extract_cvss_score(vuln),
                    "package": {
                        "name": pkg_name,
                        "version": pkg_version,
                        "type": result.get("Type", "")
                    },
                    "fixed_in": [fixed_version] if fixed_version else [],
                    "target": target,
                    "cve": cve_list,
                    "cwe": cwe_ids,
                    "references": refs,  # ← Liste propre garantie
                    "publication_time": pub_time,
                    "last_modified_time": mod_time,
                    "mitigation_recommendation": recommendation
                }

                # INJECTION DU BLOC UNIFIED
                normalized_vuln['unified'] = self._create_unified_block(
                    tool_id=vuln_id or f"trivy:unknown",
                    tool_type=vuln_type,
                    severity=mapped_severity,
                    score=self._extract_cvss_score(vuln) or self._get_severity_score(mapped_severity),
                    is_security_issue=True,
                    is_vulnerability=True,
                    category='security',
                    is_fixable=has_fix,
                    fix_version=fixed_version,
                    can_auto_upgrade=False,
                    is_exploitable=False,
                    exploit_maturity='not-applicable',
                    component=package_full,
                    location=target + (f" ({result.get('Type')})" if result.get('Type') else ""),
                    creation_time=pub_time,
                    current_time=scan_end_time
                )

                normalized["vulnerabilities"].append(normalized_vuln)

        normalized["metadata"]["trivy"] = {
            "schema_version": data.get("SchemaVersion", 0),
            "artifact_name": data.get("ArtifactName", ""),
            "artifact_type": data.get("ArtifactType", ""),
            "targets_analyzed": len(results)
        }

        normalized["summary"]["severity_distribution"] = {
            "critical": normalized["summary"]["critical"],
            "high": normalized["summary"]["high"],
            "medium": normalized["summary"]["medium"],
            "low": normalized["summary"]["low"]
        }

        return normalized

    def _normalize_sonarqube(self, data: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
        """Normalisation SonarQube avec extraction recommandations et comptage centralisé."""

        detailed_issues = data.get("detailed_issues", [])
        quality_gate_status = data.get("status", "UNKNOWN")
        scan_end_time = normalized.get("@timestamp")

        # Normaliser "ERROR" → "FAILED" (Le statut SonarQube "ERROR" dans votre JSON est l'équivalent de FAILED)
        if quality_gate_status == "OK":
            quality_gate_status = "PASSED"
        elif quality_gate_status == "ERROR" or quality_gate_status == "FAILED":
            quality_gate_status = "FAILED"
        else:
            quality_gate_status = "UNKNOWN"

        print(f" Quality Gate Status détecté: {quality_gate_status}")

        # MAPPAGE DES SÉVÉRITÉS VERS ECS (Blocker et Critical map vers 'critical' ECS)
        severity_map = {
            "BLOCKER": "critical",
            "CRITICAL": "critical", # ECS Critical (pour les Hotspots, Bugs Critiques)
            "MAJOR": "high",        # ECS High (pour les Majors)
            "MINOR": "medium",      # ECS Medium (pour les Minors)
            "INFO": "low"           # ECS Low (pour les Infos)
        }

        # CALCUL CENTRALISÉ DES COMPTEURS (Issues OPEN uniquement)

        # Compteurs ECS standards (criticial, high, medium, low)
        normalized["summary"]["critical"] = 0
        normalized["summary"]["high"] = 0
        normalized["summary"]["medium"] = 0
        normalized["summary"]["low"] = 0

        # Compteurs détaillés SonarQube (pour une distribution claire)
        sonar_severity_counts = {
            "blocker": 0,
            "critical": 0,
            "major": 0,
            "minor": 0,
            "info": 0
        }

        open_type_counts = {
            "bugs": 0,
            "vulnerabilities": 0,
            "code_smells": 0,
            "security_hotspots": 0
        }

        normalized_issues_list = []

        # Filtrer uniquement les issues 'OPEN'
        open_issues = [issue for issue in detailed_issues if issue.get("status") == "OPEN"]

        print(f" Issues totales brutes: {len(detailed_issues)}, Issues OPEN: {len(open_issues)}")

        for issue in open_issues:
            issue_type = issue.get("type", "").upper()
            severity_sonar = issue.get("severity", "").upper()

            # Déterminer la sévérité normalisée (ECS)
            severity_ecs = severity_map.get(severity_sonar, "low")

            # 1. Incrémentation des compteurs par TYPE
            if issue_type == "BUG":
                open_type_counts["bugs"] += 1
            elif issue_type == "VULNERABILITY":
                open_type_counts["vulnerabilities"] += 1
            elif issue_type == "CODE_SMELL":
                open_type_counts["code_smells"] += 1
            elif issue_type == "SECURITY_HOTSPOT":
                # Les Hotspots ne sont pas des issues classiques, les compter séparément
                open_type_counts["security_hotspots"] += 1
                continue # Passer l'incrémentation des compteurs ECS pour les Hotspots

            # 2. Incrémentation des compteurs par SÉVÉRITÉ (ECS)
            if severity_ecs == "critical":
                normalized["summary"]["critical"] += 1
            elif severity_ecs == "high":
                normalized["summary"]["high"] += 1
            elif severity_ecs == "medium":
                normalized["summary"]["medium"] += 1
            elif severity_ecs == "low":
                normalized["summary"]["low"] += 1

            # 3. Incrémentation des compteurs par SÉVÉRITÉ (SonarQube pour distribution détaillée)

            if severity_sonar == "BLOCKER":
                sonar_severity_counts["blocker"] += 1
            elif severity_sonar == "CRITICAL":
                sonar_severity_counts["critical"] += 1
            elif severity_sonar == "MAJOR":
                sonar_severity_counts["major"] += 1
            elif severity_sonar == "MINOR":
                sonar_severity_counts["minor"] += 1
            elif severity_sonar == "INFO":
                sonar_severity_counts["info"] += 1

            # 4. Création du document de vulnérabilité normalisé (pour le tableau 'vulnerabilities')
            recommendation = self._extract_sonarqube_recommendation(issue)

            # --- SonarQube-specific fields for unified ---
            is_vulnerability = (issue_type == "VULNERABILITY" or issue_type == "SECURITY_HOTSPOT")
            is_security_issue = is_vulnerability or issue_type == "BUG"
            category = 'security' if is_security_issue else 'quality'

            component_path = issue.get("component", "").split(':')[-1] # Exclure le projectKey initial
            line_number = issue.get("line")
            location = f"{component_path}:{line_number}" if line_number else component_path
            # ---------------------------------------

            normalized_vuln = {
                # ... (Les autres champs restent inchangés)
                "id": issue.get("key", ""),
                "title": issue.get("message", ""),
                "severity": severity_ecs,
                "original_severity": severity_sonar.lower(), # Ajout du niveau SonarQube (BLOCKER, CRITICAL)
                "type": issue_type.lower(),
                "component": issue.get("component", ""),
                "line": issue.get("line", 0),
                "status": issue.get("status", "OPEN"),
                "resolution": issue.get("resolution", ""),
                "debt": issue.get("debt", ""),
                "tags": issue.get("tags", []),
                "creation_date": issue.get("creationDate", None),
                "update_date": issue.get("updateDate", None),
                "mitigation_recommendation": recommendation
            }

            # INJECTION DU BLOC UNIFIED
            normalized_vuln['unified'] = self._create_unified_block(
                tool_id=issue.get("key", f"sonarqube:unknown"),
                tool_type=issue_type.lower(),
                severity=severity_ecs,
                score=self._get_severity_score(severity_ecs),
                is_security_issue=is_security_issue,
                is_vulnerability=is_vulnerability,
                category=category,
                is_fixable=True, # Toutes les issues SonarQube sont conceptuellement 'fixables'
                fix_version='',
                can_auto_upgrade=False,
                is_exploitable=False,
                exploit_maturity='not-applicable',
                component=component_path,
                location=location,
                creation_time=issue.get("creationDate"),
                current_time=scan_end_time
            )

            normalized_issues_list.append(normalized_vuln)

        # MISE À JOUR DU CHAMP SUMMARY

        # Total des failles comptées (Bugs + Vulnerabilities + Code Smells + Hotspots)
        normalized["summary"]["total_vulnerabilities"] = (
                open_type_counts["bugs"] +
                open_type_counts["vulnerabilities"] +
                open_type_counts["code_smells"] +
                open_type_counts["security_hotspots"]
        )

        # Remplissage du tableau des issues
        normalized["vulnerabilities"] = normalized_issues_list

        # MISE À JOUR DES MÉTRADONNÉES ET MESURES GLOBALES (unchanged)
        # ... (le code pour global_measures, metrics, metadata reste inchangé)

        # Distribution détaillée des sévérités/types (Réponse à votre besoin de clarté)
        normalized["summary"]["severity_distribution"] = {
            "bugs": open_type_counts["bugs"],
            "vulnerabilities": open_type_counts["vulnerabilities"],
            "code_smells": open_type_counts["code_smells"],
            "security_hotspots": open_type_counts["security_hotspots"],
            # Distribution précise SonarQube
            "blocker": sonar_severity_counts["blocker"],
            "critical_sonar": sonar_severity_counts["critical"],
            "major": sonar_severity_counts["major"],
            "minor": sonar_severity_counts["minor"],
            "info": sonar_severity_counts["info"],
            # Compteurs ECS agrégés (pour le Watcher)
            "critical_ecs": normalized["summary"]["critical"],
            "high_ecs": normalized["summary"]["high"],
            "medium_ecs": normalized["summary"]["medium"],
            "low_ecs": normalized["summary"]["low"]
        }

        # Le reste du code...
        global_measures = data.get("global_measures", [])
        measures_dict = {m.get("metric"): m.get("value") for m in global_measures}

        # ... (Répéter le reste du code de la fonction pour la complétude)
        normalized["metadata"]["sonarqube"] = {
            "project_key": data.get("projectKey", ""),
            "project_name": data.get("projectName", ""),
            "quality_gate": quality_gate_status
        }

        rating_map = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E", "1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E"}

        normalized["metrics"]["quality"] = {
            "coverage": float(measures_dict.get("coverage", 0)),
            "duplicated_lines_density": float(measures_dict.get("duplicated_lines_density", 0)),
            "technical_debt_minutes": int(measures_dict.get("sqale_index", 0)),
            "maintainability_rating": rating_map.get(measures_dict.get("sqale_rating", ""), measures_dict.get("sqale_rating", "A")),
            "reliability_rating": rating_map.get(measures_dict.get("reliability_rating", ""), measures_dict.get("reliability_rating", "A")),
            "security_rating": rating_map.get(measures_dict.get("security_rating", ""), measures_dict.get("security_rating", "A")),
            "lines_of_code": int(measures_dict.get("ncloc", 0))
        }


        return normalized

    # NOUVELLES FONCTIONS : EXTRACTION RECOMMANDATIONS

    def _extract_snyk_recommendation(self, vuln: Dict[str, Any]) -> str:
        """Extraire recommandation de mitigation depuis Snyk"""

        # Priorité 1 : Upgrade path
        if vuln.get("isUpgradable") and vuln.get("fixedIn"):
            fixed_version = vuln["fixedIn"][0] if isinstance(vuln["fixedIn"], list) else vuln["fixedIn"]
            pkg_name = vuln.get("packageName", "package")
            return f"Upgrade {pkg_name} to version {fixed_version}"

        # Priorité 2 : Patch disponible
        if vuln.get("isPatchable"):
            return "Apply available security patch"

        # Priorité 3 : Description avec fix
        description = vuln.get("description", "")
        if "upgrade" in description.lower() or "update" in description.lower():
            # Extraire première phrase avec upgrade/update
            sentences = description.split('.')
            for sentence in sentences:
                if "upgrade" in sentence.lower() or "update" in sentence.lower():
                    return sentence.strip()

        # Fallback
        return "Review Snyk security advisory for remediation steps"

    def _extract_trivy_recommendation(self, vuln: Dict[str, Any]) -> str:
        """Extraire recommandation de mitigation depuis Trivy"""

        # Priorité 1 : Fixed version disponible
        fixed_version = vuln.get("FixedVersion")
        if fixed_version:
            pkg_name = vuln.get("PkgName", "package")
            return f"Update {pkg_name} to version {fixed_version} or later"

        # Priorité 2 : Pas de fix disponible
        pkg_name = vuln.get("PkgName", "package")
        return f"No fix available yet for {pkg_name}. Monitor security advisories or consider alternative packages"

    def _extract_sonarqube_recommendation(self, issue: Dict[str, Any]) -> str:
        """Extraire recommandation de mitigation depuis SonarQube"""

        issue_type = issue.get("type", "").upper()
        message = issue.get("message", "")

        # Pour code duplication
        if "duplicat" in message.lower():
            return "Refactor code to extract duplicated logic into reusable functions or utility classes"

        # Pour bugs
        if issue_type == "BUG":
            return f"Fix bug: {message}. Review SonarQube rule documentation for detailed guidance"

        # Pour vulnérabilités
        if issue_type == "VULNERABILITY":
            return f"Security issue: {message}. Apply secure coding practices as per SonarQube recommendations"

        # Pour code smells
        if issue_type == "CODE_SMELL":
            return f"Improve code quality: {message}"

        # Pour security hotspots
        if issue_type == "SECURITY_HOTSPOT":
            return f"Review security hotspot: {message}. Verify if this code path is exploitable"

        # Fallback
        return f"Review and fix: {message}"

    #NOUVELLE FONCTION : CALCUL MTTD SUR 7 JOURS GLISSANTS

    def _calculate_mttd(self, normalized: Dict[str, Any]) -> Dict[str, Any]:

        scan_end_time = self.metadata.get("scan_end_time")

        intro_time = self.metadata.get("code_introduction_time")

        if not intro_time or not scan_end_time:
            print(" code_introduction_time manquant dans les métadonnées")
            normalized["metrics"]["mttd"]["build_data"] = {
                "is_calculated": False,
                "reason": "time_data_missing"
            }
            return normalized
        try:
            if isinstance(intro_time, str):
                intro_time = int(intro_time)
            if isinstance(scan_end_time, str):
                scan_end_time = int(scan_end_time)
        except ValueError:
            print(f" Erreur de conversion de timestamp: intro={intro_time}, end={scan_end_time}")
            normalized["metrics"]["mttd"]["build_data"] = {
                "is_calculated": False,
                "reason": "time_data_invalid"
            }
            return normalized

        # Calculer MTTD actuel (pour ce build)
        mttd_ms = scan_end_time - intro_time

        if mttd_ms < 0:
            print(f" MTTD négatif ({mttd_ms}ms), probable erreur de timestamp")
            mttd_ms = 0

        total_scan_duration_hours = mttd_ms / (1000 * 3600)
        total_scan_duration_min = mttd_ms / (1000 * 60)

        #Récupérer le nombre de vulnérabilités (N)
        num_vulnerabilities = normalized["summary"].get("total_vulnerabilities", 0)

        #Calcul du MTTD-CI (temps MOYEN par vulnérabilité)
        if num_vulnerabilities > 0:
            mttd_ci_hours = total_scan_duration_hours / num_vulnerabilities
            mttd_ci_min = total_scan_duration_min / num_vulnerabilities
        else:
            # Si aucune vulnérabilité, on peut choisir d'utiliser 0 ou la durée totale,
            # mais la meilleure pratique est d'utiliser 0 pour éviter de fausser les moyennes globales.
            mttd_ci_hours = 0.0
            mttd_ci_min = 0.0

        # --- Création de la structure d'entrée stable ---
        mttd_build_entry = {
            "mttd_hours": round(mttd_ci_hours, 4),
            "mttd_min": round(mttd_ci_min, 4),
            "total_scan_duration_hours": round(total_scan_duration_hours, 4),
            "num_vulnerabilities": num_vulnerabilities,
            "code_introduction_time": intro_time,
            "scan_end_time": scan_end_time,
            "is_calculated": True
        }

        # --- Affectation finale dans normalized["metrics"]["mttd"] ---
        # Utilisation de la clé stable "build_data" pour stocker la métrique
        normalized["metrics"]["mttd"]["build_data"] = mttd_build_entry

        print(f" MTTD-CI calculé pour {self.tool} ({self.metadata.get('service')}): {mttd_ci_hours:.4f} heures/vulnérabilité")

        return normalized

    def _initialize_mttr(self, normalized: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialise la structure MTTR (sera calculé par le watcher auto-resolve)
        """

        normalized["metrics"]["mttr"] = {
            "sonarqube": None,
            "snyk": None,
            "trivy": None,
            "note": "MTTR will be calculated by watcher when vulnerabilities are resolved"
        }

        return normalized

    # ========================================================================
    # FONCTIONS UTILITAIRES (PRÉSERVÉES)
    # ========================================================================

    def _get_severity_score(self, severity: str) -> float:
        """Mappe une sévérité texte (ECS) vers un score numérique (échelle 1-10)"""
        severity_map = {'critical': 10.0, 'high': 7.0, 'medium': 5.0, 'low': 3.0, 'info': 1.0, 'unknown': 1.0}
        return severity_map.get(severity.lower(), 1.0)

    def _create_unified_block(self, tool_id: str, tool_type: str, severity: str, score: float,
                              is_security_issue: bool, is_vulnerability: bool, category: str,
                              is_fixable: bool, fix_version: str, can_auto_upgrade: bool,
                              is_exploitable: bool, exploit_maturity: str, component: str,
                              location: str, creation_time: Optional[str], current_time: str) -> Dict[str, Any]:
        """Crée le bloc 'unified' standardisé et sécurisé pour une vulnérabilité."""

        # Ces champs proviennent de self.metadata (la seule source de vérité dans ce script)
        assignee_email = self.metadata.get("git_author", "DevTeam")
        service_name = self.metadata.get("service", "unknown")

        # Définition de la date sentinelle (Époque UNIX)
        DEFAULT_SENTINEL_DATE = "1970-01-01T00:00:00Z"

        return {
            'vulnerability_id': tool_id,
            'type': tool_type,
            'severity': severity.lower(),
            'severity_score': round(float(score), 2),
            'is_security_issue': is_security_issue,
            'is_vulnerability': is_vulnerability,
            'category': category,
            'is_fixable': is_fixable,
            'has_fix_available': is_fixable,
            'fix_version': fix_version or '',
            'can_auto_upgrade': can_auto_upgrade,
            'is_exploitable': is_exploitable,
            'exploit_maturity': exploit_maturity,
            'component': component,
            'location': location,
            'assignee': assignee_email,
            'team': f"{service_name}-team",
            'status': 'open',
            'first_seen': creation_time or current_time,
            'last_seen': current_time,
            'resolution_date': DEFAULT_SENTINEL_DATE,
            'age_days': 0,
            'mttr_hours': 0.0
        }


    def _extract_tool_version(self, data: Dict[str, Any]) -> str:
        """Extrait la version de l'outil depuis le rapport"""
        if self.tool == "snyk":
            return data.get("version", "unknown")
        elif self.tool == "trivy":
            return str(data.get("SchemaVersion", "unknown"))
        elif self.tool == "sonarqube":
            return "9.9.8"
        return "unknown"

    def _extract_cvss_score(self, vuln: Dict[str, Any]) -> float:
        """Extrait le score CVSS depuis différents formats"""
        if "CVSS" in vuln:
            cvss_data = vuln["CVSS"]
            if isinstance(cvss_data, dict):
                for vendor in ["nvd", "redhat"]:
                    if vendor in cvss_data:
                        v3_score = cvss_data[vendor].get("V3Score")
                        if v3_score:
                            return float(v3_score)
        return 0.0


def save_normalized_report_atomic(data: Dict[str, Any], output_file: str) -> None:
    """
    Sauvegarde atomique (évite lectures partielles par Filebeat)

    1. Écrire dans .tmp
    2. Renommer atomiquement
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    temp_file = output_file + '.tmp'

    try:
        print(f" Écriture temporaire: {temp_file}")
        with open(temp_file, 'w', encoding='utf-8') as f:
            json_line = json.dumps(data, ensure_ascii=False)
            f.write(json_line + "\n")
            f.flush()
            os.fsync(f.fileno())

        print(f" Renommage atomique: {temp_file} → {output_file}")
        os.rename(temp_file, output_file)

        print(f" Rapport normalisé sauvegardé: {output_file}")

    except Exception as e:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                print(f" Fichier temporaire supprimé après erreur")
            except:
                pass
        raise IOError(f" Erreur lors de la sauvegarde atomique: {e}")


def main():
    """Point d'entrée du script"""

    if len(sys.argv) < 5:
        print("Usage: python3 normalize-reports.py <input> <output> <tool> <metadata_json>")
        print("\nExemple:")
        print('  python3 normalize-reports.py input.json output.json snyk \'{"build_id":"123"}\'')
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    tool = sys.argv[3]
    metadata_json = sys.argv[4]

    try:
        if not os.path.exists(input_file):
            print(f" Fichier d'entrée introuvable: {input_file}")
            sys.exit(1)

        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError as e:
            print(f" JSON métadonnées invalide: {e}")
            sys.exit(1)

        print(f" Lecture du rapport: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        print(f" Normalisation avec l'outil: {tool}")
        normalizer = ReportNormalizer(tool, metadata)
        normalized_data = normalizer.normalize(raw_data)

        save_normalized_report_atomic(normalized_data, output_file)

        # Statistiques
        print(f"\n Statistiques:")
        print(f"  • Vulnérabilités détectées: {normalized_data['summary']['total_vulnerabilities']}")
        print(f"  • Critical: {normalized_data['summary']['critical']}")
        print(f"  • High: {normalized_data['summary']['high']}")
        print(f"  • Medium: {normalized_data['summary']['medium']}")
        print(f"  • Low: {normalized_data['summary']['low']}")

        if normalized_data['metrics']['mttd'].get('current_build', {}).get('is_calculated'):
            mttd_hours = normalized_data['metrics']['mttd']['current_build']['mttd_hours']
            print(f"  • MTTD: {mttd_hours} heures")

        print(f"\n Normalisation terminée avec succès")
        sys.exit(0)

    except Exception as e:
        print(f"\n Erreur fatale: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()