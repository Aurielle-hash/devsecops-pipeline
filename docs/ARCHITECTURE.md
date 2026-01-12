
# 🏗️ Architecture Technique Détaillée

## Vue d'Ensemble

L'architecture implémente le principe **Security as Code** en intégrant les outils de sécurité directement dans le CI/CD. Elle repose sur 3 couches logiques :

1. **Couche d'Orchestration** (Jenkins + Docker)
2. **Couche de Contrôle** (Security Gates - Shift Left)
3. **Couche d'Observabilité** (Elastic Stack)

## Architecture Globale

![Architecture Cible](images/Global_Architecture.png)


```mermaid
graph TB
    subgraph "1. Source Control"
        A[GitLab Repository]
    end
    
    subgraph "2. CI/CD Orchestration"
        B[Jenkins Master]
        C[Jenkins Agent<br/>Docker Container]
    end
    
    subgraph "3. Security Scanning"
        D[SonarQube<br/>SAST]
        E[Snyk<br/>SCA]
        F[Trivy<br/>Container Scan]
    end
    
    subgraph "4. Data Processing"
        G[Normalize Script<br/>Python + ECS]
        H[Split Script<br/>Parent/Child]
    end
    
    subgraph "5. Observability Stack"
        I[Filebeat<br/>Log Shipper]
        J[Metricbeat<br/>Metrics Collector]
        K[APM Server<br/>Traces]
        L[Elasticsearch<br/>Data Store]
        M[Kibana<br/>Visualization]
    end
    
    subgraph "6. Alerting & Response"
        N[Watcher 1<br/>MTTR Calculator]
        O[Watcher 2<br/>Slack Notifier]
        P[Slack Channel]
    end
    
    A -->|Webhook| B
    B --> C
    C -->|Scan| D
    C -->|Scan| E
    C -->|Scan| F
    D -->|JSON| G
    E -->|JSON| G
    F -->|JSON| G
    G --> H
    H --> I
    I --> L
    J --> L
    K --> L
    L --> M
    L --> N
    N --> O
    O --> P
    
    style D fill:#ff6b6b
    style E fill:#ff6b6b
    style F fill:#ff6b6b
    style L fill:#4ecdc4
    style M fill:#4ecdc4
```

## Flux de Données Détaillé

### Phase 1 : Déclenchement

```mermaid
sequenceDiagram
    participant Dev as Développeur
    participant GL as GitLab
    participant JM as Jenkins Master
    participant JA as Jenkins Agent
    
    Dev->>GL: git push
    GL->>JM: Webhook POST
    JM->>JA: Trigger Pipeline
    Note over JA: Capture T0<br/>(Code Introduction Time)
```

### Phase 2 : Build & Scan

```mermaid
sequenceDiagram
    participant JA as Jenkins Agent
    participant SQ as SonarQube
    participant SN as Snyk
    participant TR as Trivy
    participant FS as File System
    
    JA->>JA: git clone
    JA->>JA: mvn clean install
    par Parallel Scans
        JA->>SQ: SAST Analysis
        SQ-->>FS: issues.json
    and
        JA->>SN: SCA Analysis
        SN-->>FS: vulnerabilities.json
    and
        JA->>TR: Container Scan
        TR-->>FS: trivy-report.json
    end
    Note over FS: /shared/build-N/<br/>sonar/snyk/trivy
```

### Phase 3 : Normalisation & Ingestion

```mermaid
sequenceDiagram
    participant FS as File System
    participant PY1 as normalize_reports.py
    participant PY2 as split_reports.py
    participant FB as Filebeat
    participant ES as Elasticsearch
    
    PY1->>FS: Lire rapports bruts
    PY1->>PY1: Convertir vers ECS
    PY1->>FS: Écrire report.json
    PY2->>FS: Lire report.json
    PY2->>PY2: Découpage Parent/Enfant
    PY2->>FS: Écrire report.ndjson
    FB->>FS: Scan (10s interval)
    FB->>FB: Parse JSON
    FB->>ES: Bulk Index
    ES->>ES: Ingest Pipeline
    ES->>ES: Template Mapping
```

### Phase 4 : Observabilité

```mermaid
graph TB
    A[Elasticsearch] --> B[Kibana]
    B --> C[Dashboard 1: Security Unified]
    B --> D[Dashboard 2: Snyk SCA]
    B --> E[Dashboard 3: Trivy Containers]
    B --> F[Dashboard 4: SonarQube SAST]
    B --> G[Dashboard 5: Metricbeat Infra]
    B --> H[Dashboard 6: APM Performance]
    
    A --> I[Watcher 1: Mark Resolved]
    I --> J[Calcul MTTR]
    J --> K[Document resolved_report]
    
    A --> L[Watcher 2: Vulnerability Report]
    L --> M[Lecture resolved_report]
    L --> N[Triage Ouvert vs Résolu]
    N --> O[Slack Webhook]
```

## Composants Détaillés

### Jenkins Agent Custom

**Dockerfile** : Basé sur `jenkins/jenkins:lts`

**Outils embarqués** :
- Docker CLI (DinD via socket mount)
- Maven 3.8.4
- Node.js 18
- PHP + Composer
- Snyk CLI
- Trivy
- Python 3 + scripts

**Justification** : Évite l'installation manuelle, garantit reproductibilité

### Elasticsearch : Architecture d'Ingestion

```mermaid
graph LR
    A[Filebeat] -->|JSON Logs| B[Ingest Node]
    B --> C{Pipeline?}
    C -->|snyk_pipeline| D[Processor 1]
    C -->|trivy_pipeline| E[Processor 2]
    C -->|sonar_pipeline| F[Processor 3]
    D --> G[Index Node]
    E --> G
    F --> G
    G --> H[(Shard 1)]
    G --> I[(Shard 2)]
```

**3 Ingest Pipelines** :
- Renommage champs
- Enrichissement métadonnées
- Calcul scores de risque

**Index Template** :
- Mapping `nested` pour Parent
- Mapping `flat` pour Enfants
- Dynamic templates pour absorption variations

### Modèle Parent/Enfant

**Problème** : Kibana ne peut pas visualiser les champs `nested` directement.

**Solution** : Découpage en 2 types de documents partageant le même `report_id`.

```json
// Document Parent (doc_type: vulnerability_report)
{
  "report_id": "build-123",
  "vulnerabilities": [  // <- nested field
    {"id": "CVE-2024-1234", "severity": "high"},
    {"id": "SNYK-JS-2024-5678", "severity": "critical"}
  ]
}

// Documents Enfants (doc_type: vulnerability_finding)
{
  "report_id": "build-123",
  "vulnerability_id": "CVE-2024-1234",
  "severity": "high"
}
{
  "report_id": "build-123",
  "vulnerability_id": "SNYK-JS-2024-5678",
  "severity": "critical"
}
```

**Avantages** :
- Parent → Watchers (analyses complexes)
- Enfants → Kibana (visualisations)
- Corrélation via `report_id`