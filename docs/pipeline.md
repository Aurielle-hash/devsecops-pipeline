
# ⚙️ Pipeline CI/CD

Documentation du pipeline Jenkins.

## Jenkinsfile Structure

7 stages séquentiels :
```markdown
1. **Checkout & Git Metadata** : Clone + capture T0
2. **Build & SAST Backend** : Maven + SonarQube
3. **Build & SAST Frontend** : NPM + ESLint
4. **Containerization** : Docker build images
5. **Security Scan Images** : Trivy scan
6. **Push Docker Images** : Registry push
7. **Attente Ingestion Filebeat** : Sleep 30s

## Triggers

- **Webhook GitLab** : Sur push vers `main`
- **Manuel** : Via UI Jenkins

## Variables d'Environnement
```

```groovy
SNYK_TOKEN = credentials('snyk-api')
SONAR_TOKEN = credentials('sonar-token')
REPORTS_DIR = "/shared"
BUILD_ID = env.BUILD_NUMBER
```
## Quality Gates

Pipeline **FAIL** si :
- SonarQube Quality Gate FAILED
- Snyk détecte CVE critiques > seuil
- Build Maven/NPM échoue

## Artefacts Générés

- `/shared/build-N/sonarqube/scans/backend.json`
- `/shared/build-N/snyk/backend.json`
- `/shared/build-N/trivy/backend.json`
