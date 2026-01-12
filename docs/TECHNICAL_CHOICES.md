
# 🎯 Choix Techniques & Justifications

Ce document explique le **"Pourquoi"** derrière chaque décision technique majeure du projet.

## Contexte & Contraintes

### Contraintes Initiales

| Type | Contrainte | Impact |
|------|-----------|---------|
| **Budgétaire** | 100% open-source | Exclusion SaaS propriétaires (SonarCloud, Snyk payant) |
| **Organisationnelle** | Pas d'équipe DevOps dédiée | Solution autonome, simple à maintenir |
| **Technique** | Absence de CI/CD et Docker | Construction from scratch |
| **Humaine** | Développeurs peu sensibilisés sécurité | UX développeur prioritaire (feedback rapide) |
| **Déploiement** | VM unique pour PoC | Infrastructure légère (Docker Compose > K8s) |

---

## 1. Orchestrateur CI/CD

### ✅ Choix : Jenkins

**Alternatives évaluées** : GitLab CI, GitHub Actions, CircleCI

| Critère | Jenkins | GitLab CI | GitHub Actions |
|---------|---------|-----------|----------------|
| **Coût** | 100% gratuit | Limites minutes gratuit | Limites minutes gratuit |
| **Flexibilité** | Pipeline as Code (Groovy) | YAML simple | YAML + Marketplace |
| **Écosystème Plugins** | 1800+ plugins | Intégré GitLab | Actions Marketplace |
| **Courbe apprentissage** | Moyenne | Facile | Facile |
| **Maturité** | Leader depuis 2011 | Mature | Plus récent |

**Justifications** :
1. **Zéro coût** : Pas de limite de build minutes (contrainte budgétaire)
2. **Flexibilité totale** : Jenkinsfile permet logique complexe (Groovy) vs YAML limité
3. **Écosystème plugins** : 1800+ dont SonarQube Scanner, Docker, Git, Slack
4. **Standard industrie** : CV skills + documentation abondante
5. **Auto-hébergé** : Contrôle total données sensibles (code, rapports sécurité)

**Trade-off accepté** : Interface datée, configuration initiale plus complexe

**Référence mémoire** : Tableau 3.2 (page 19)

---

## 2. SAST (Static Application Security Testing)

### ✅ Choix : SonarQube Community

**Alternatives évaluées** : SonarCloud, Checkmarx, Veracode

| Critère | SonarQube CE | SonarCloud | Checkmarx |
|---------|--------------|------------|-----------|
| **Coût** | Gratuit | Gratuit (limité) | Licence €€€€ |
| **Langages supportés** | 29 | 29 | 30+ |
| **Quality Gates** | ✅ | ✅ | ✅ |
| **Déploiement** | On-premise | SaaS | On-premise/SaaS |
| **Base de données** | PostgreSQL requise | N/A | Oracle/SQL Server |

**Justifications** :
1. **Leader du SAST** : 7M+ développeurs, référence marché
2. **Gratuit & complet** : Community Edition inclut Quality Gates, 29 langages
3. **Quality Gates bloquants** : Intégration CI/CD native, bloque merge si seuils non atteints
4. **Règles de qualité** : Bugs, Vulnerabilities, Code Smells, Technical Debt
5. **Communauté active** : Documentation riche, support forum

**Trade-off accepté** : Consommation RAM (2-4 GB), besoin PostgreSQL

**Pourquoi pas SonarCloud ?** : Limites projets privés version gratuite, données hébergées externe

**Référence mémoire** : Tableau 3.3 (page 21), Section 3.5.3

---

## 3. SCA (Software Composition Analysis)

### ✅ Choix : Snyk CLI (Free Tier)

**Alternatives évaluées** : OWASP Dependency-Check, GitHub Dependabot

| Critère | Snyk | OWASP Dep-Check | Dependabot |
|---------|------|-----------------|------------|
| **Coût** | 200 tests/mois gratuit | 100% gratuit | Gratuit GitHub |
| **Base CVE** | Propriétaire + NVD | NVD | NVD + GitHub |
| **Exploitability** | ✅ Maturity Score | ❌ | ✅ |
| **Fix automatiques** | ✅ PR auto | ❌ | ✅ PR auto |
| **CLI** | ✅ | ✅ | ❌ (GitHub only) |

**Justifications** :
1. **Contexte d'exploitabilité** : Snyk fournit `exploitMaturity` (Proof of Concept, No Known Exploit, Mature) → Priorisation intelligente
2. **Base de données propriétaire** : Mise à jour plus rapide que NVD
3. **Fix recommendations** : Snyk propose versions cibles pour upgrade
4. **200 tests/mois gratuit** : Suffisant pour PoC (1 test/build × 30 jours × 6 projets)
5. **CLI simple** : `snyk test --json` → intégration Jenkins triviale

**Trade-off accepté** : Dépendance cloud pour analyse (CLI envoie manifests à Snyk API)

**Pourquoi pas OWASP Dependency-Check ?** : Plus lent (5-10min vs 30s), taux faux positifs élevé, pas d'exploitability

**Référence mémoire** : Tableau 3.4 (page 22), Section 3.5.4

---

## 4. Container Security Scanning

### ✅ Choix : Trivy

**Alternatives évaluées** : Clair, Anchore Engine, Grype

| Critère | Trivy | Clair | Anchore |
|---------|-------|-------|---------|
| **Coût** | 100% gratuit | Gratuit | Freemium |
| **Vitesse** | Très rapide | Moyen | Lent |
| **Setup** | Binaire Go standalone | PostgreSQL requis | Architecture complexe |
| **OS + App** | ✅ | ✅ | ✅ |
| **Secrets scanning** | ✅ | ❌ | ❌ |

**Justifications** :
1. **Simplicité déploiement** : Binaire unique Go, pas de dépendances
2. **Rapidité** : Scan complet en < 30s (vs 2-5min Clair)
3. **Détection exhaustive** : OS packages (apt, yum, apk) + dépendances app (npm, pip, gem)
4. **Secrets scanning** : Détecte credentials hardcodés (AWS keys, tokens)
5. **Output JSON structuré** : Facile à parser et normaliser

**Trade-off accepté** : Base CVE légèrement moins complète que Clair (mais 99% use cases couverts)

**Référence mémoire** : Tableau 3.5 (page 23), Section 3.5.5

---

## 5. Plateforme d'Observabilité

### ✅ Choix : Elastic Stack (ELK)

**Alternatives évaluées** : Splunk Free, Graylog, Prometheus + Grafana

| Critère | Elastic Stack | Splunk Free | Graylog | Prometheus/Grafana |
|---------|---------------|-------------|---------|-------------------|
| **Coût** | Licence Basic gratuite | 500 MB/jour | Gratuit | Gratuit |
| **Logs** | ✅ Elasticsearch | ✅ | ✅ | ❌ (metrics only) |
| **Metrics** | ✅ Metricbeat | ✅ | Limité | ✅ Prometheus |
| **APM** | ✅ Intégré | ❌ | ❌ | ✅ Tempo/Jaeger |
| **SIEM** | ✅ | ✅ | ❌ | ❌ |

**Justifications** :
1. **Tout-en-un** : Logs (Filebeat), Metrics (Metricbeat), Traces (APM), Alerting (Watcher) dans 1 stack
2. **Licence Basic gratuite** : Inclut Watcher (alerting), Canvas, Maps (vs Splunk limité 500MB/jour)
3. **Elasticsearch : moteur puissant** : Requêtes full-text, agrégations complexes, nested queries
4. **Kibana : dashboards flexibles** : Création visuelle sans code
5. **Elastic Common Schema (ECS)** : Standard de normalisation reconnu

**Trade-offs acceptés** :
- Consommation RAM élevée (4-8 GB pour stack complète)
- Complexité configuration avancée (Ingest Pipelines, Index Templates)

**Pourquoi pas Prometheus/Grafana ?** : Pas de support logs natif, nécessiterait Loki (complexité additionnelle)

**Référence mémoire** : Tableau 3.6 (page 24), Section 3.5.6

---

## 6. Conteneurisation

### ✅ Choix : Docker + Docker Compose

**Alternatives évaluées** : Kubernetes, Podman, LXC

| Critère | Docker Compose | Kubernetes | Podman |
|---------|----------------|-----------|--------|
| **Complexité** | Faible | Élevée | Moyenne |
| **PoC friendly** | ✅ | ❌ | ✅ |
| **Production scale** | Limité | ✅ | Limité |
| **Courbe apprentissage** | 1 jour | 2-3 mois | 1 semaine |
| **Écosystème** | Mature | Mature | Émergent |

**Justifications** :
1. **Standard industrie** : Docker = 90%+ parts de marché conteneurs
2. **Simplicité PoC** : Fichier YAML déclaratif, `docker-compose up` suffit
3. **Reproductibilité** : Infrastructure as Code (IaC), même environnement partout
4. **Isolation** : Chaque service dans son conteneur (résolution conflits dépendances)
5. **Portabilité** : Dev laptop → VM staging → Production sans changement

**Trade-off accepté** : Pas de HA native, pas d'orchestration avancée (acceptable pour PoC)

**Pourquoi pas Kubernetes ?** : Overkill pour VM unique, complexité excessive (Control Plane, etcd, CNI, Ingress...) pour gain nul

**Référence mémoire** : Tableau 3.7 (page 27), Section 3.5.7

---

## 7. Architecture de Données Elasticsearch

### ✅ Choix : Modèle Parent/Enfant (Découpage Externe)

**Alternatives évaluées** :
1. Documents plats seulement (1 doc = 1 vulnérabilité)
2. Nested field seulement (array dans 1 doc)
3. Parent-child relation Elasticsearch native
4. **Découpage externe via script Python** ✅

**Problème** : Kibana ne peut pas visualiser champs `nested` directement.

**Solution retenue** : Générer 2 types de documents avant ingestion

```python
# normalize_reports.py génère 1 document unifié
{
  "vulnerabilities": [...]  # Array complet
}

# split_reports.py crée N+1 documents
# 1 Parent (garde nested pour Watchers)
# N Enfants (1 par vuln, pour Kibana)
```

**Justifications** :
1. **Contrôle total** : Génération externe = structure garantie, pas d'effet de bord ES
2. **Flexibilité** : Modification schéma sans toucher Ingest Pipelines
3. **Performance Kibana** : Documents plats = visualisations instantanées
4. **Analyses complexes** : Parent nested = Watchers fonctionnent
5. **Pas de processeur `emit()`** : Version ES 7.17 ne supporte pas multi-doc emission

**Trade-off accepté** : Duplication données (1 Parent + N Enfants), mais négligeable (< 1MB par build)

**Référence mémoire** : Section 5.2.1 (page 40-42)
