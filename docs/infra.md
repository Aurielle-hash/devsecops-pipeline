# 🏗️ Infrastructure

Documentation de l'infrastructure Docker Compose.

## Fichiers

- `docker-compose.yml` : Stack complète (13 services)
- `docker-compose.prod.yml` : Overrides production
- `Dockerfile.jenkins` : Agent Jenkins custom

## Services Déployés

| Service | Image                        | Ports | Rôle |
|---------|------------------------------|-------|------|
| GitLab | gitlab-ce:16.11.10           | 8080, 2222 | SCM |
| Jenkins | Custom (voir Dockerfile)     | 8081, 50000 | CI/CD |
| SonarQube | sonarqube:9.9.8              | 9000 | SAST |
| PostgreSQL | postgres:15-alpine           | 5432 | DB SonarQube |
| Elasticsearch | elasticsearch:7.17.7         | 9200 | Data Store |
| Kibana | kibana:7.17.7                | 5601 | Visualisation |
| Filebeat | Custom (voir filebeat.yml)   | — | Log Shipper |
| Metricbeat | Custom (voir metricbeat.yml) | — | Metrics |
| APM Server | apm-server:7.17.7            | 8200 | Traces |

## Déploiement

Voir [Guide Quick Start](../README.md#-quick-start)

## Volumes Persistants

- `gitlab-data` : Dépôts Git
- `jenkins_home` : Configuration Jenkins
- `sonardb_data` : Base PostgreSQL
- `es_data` : Index Elasticsearch
- `trivy-cache` : Base CVE Trivy
