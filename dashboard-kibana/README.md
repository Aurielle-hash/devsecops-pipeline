
# 📊 Dashboards Kibana

6 dashboards préconfigurés au format NDJSON.

## Import

Kibana → Stack Management → Saved Objects → Import

## Dashboards Disponibles

1. **security-unified.ndjson**
   - Vue consolidée multi-outils
   - KPIs : Total vulns, par sévérité, top 10 critiques
   
2. **snyk-sca.ndjson**
   - Analyse dépendances
   - Focus : Packages vulnérables, exploitability
   
3. **trivy-containers.ndjson**
   - Sécurité images Docker
   - Focus : CVE par image, fix disponibles
   
4. **sonarqube-sast.ndjson**
   - Qualité code + sécurité
   - Focus : Quality Gate, dette technique
   
5. **metricbeat-infra.ndjson**
   - Santé infrastructure
   - Focus : CPU, RAM, état conteneurs
   
6. **apm-performance.ndjson**
   - Performance applicative
   - Focus : Traces, RUM, Core Web Vitals

## Captures d'Écran

Voir `docs/images/*`
