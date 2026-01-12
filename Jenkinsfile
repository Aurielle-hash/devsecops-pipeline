import groovy.json.JsonOutput

pipeline {
    agent any

    tools {
        maven 'Maven 3.8.4'
        nodejs 'NodeJS 18'
    }

    environment {
        // Credentials
        SNYK_TOKEN = credentials('snyk-api')

        // Docker
        DOCKER_REGISTRY = 'docker.io'
        IMAGE_NAME_BACKEND = 'babyfoot-backend'
        IMAGE_NAME_FRONTEND = 'babyfoot-frontend'
        IMAGE_TAG = "${BUILD_NUMBER}"
        REPORTS_DIR = "/shared"

        // Build
        BUILD_ID = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout & Git Metadata') {
            steps {
                script {

                    echo " ÉTAPE 1: Récupération du code et métadonnées Git"

                    // Récupération du code
                    checkout scm
                    def result = sh(script: 'date +%Y-%m-%d_%H-%M-%S', returnStdout: true).trim()
                    echo "La commande s'est terminée à : ${result}"

                    def commitTime = System.currentTimeMillis()

                     //  Capturer le timestamp juste après le checkout
                    env.CODE_INTRODUCTION_TIME = commitTime

                    //  Métadonnées Git sécurisées
                    env.GIT_COMMIT_HASH = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim() ?: 'unknown'
                    env.GIT_BRANCH = sh(script: "git rev-parse --abbrev-ref HEAD", returnStdout: true).trim() ?: 'main'
                    env.GIT_AUTHOR = sh(script: "git log -1 --pretty=format:'%ae'", returnStdout: true).trim() ?: 'DevTeam'

                    echo " Code Introduction Time: ${env.CODE_INTRODUCTION_TIME}"
                    echo " Commit: ${env.GIT_COMMIT_HASH}"
                    echo " Branch: ${env.GIT_BRANCH}"
                    echo " Auteur: ${env.GIT_AUTHOR}"
                 }
            }
        }

        stage('Build & SAST Backend') {
            steps {
                script {
                    echo " ÉTAPE 2: Build et Analyse Backend"

                    dir('BabyFOOT/backend') {

                        echo "Compilation Maven..."
                        sh 'mvn clean install -DskipTests'

                        // SONARQUBE BACKEND
                        echo "\nAnalyse SonarQube Backend..."
                        def sonarProjectKey = "babyfoot-backend"
                        def sonarReportDir = "${REPORTS_DIR}/build-${BUILD_NUMBER}/sonarqube/scans"
                        def sonarScanStart = System.currentTimeMillis()

                        withSonarQubeEnv('SonarQube') {
                            sh "mkdir -p ${sonarReportDir}"

                            // Analyse SonarQube
                            sh """
                                mvn sonar:sonar \
                                    -Dsonar.projectKey=${sonarProjectKey} \
                                    -Dsonar.projectName="Babyfoot Backend" \
                                    -Dsonar.java.binaries=target/classes \
                                    -Dsonar.sources=src/main/java
                            """

                            // Attendre le traitement
                            echo "Attente du traitement SonarQube ..."
                            sleep(45)

                            def sonarScanEnd = System.currentTimeMillis()

                            // Récupérer les issues
                            sh """
                                curl -s -u \${SONAR_AUTH_TOKEN}: \
                                    "\${SONAR_HOST_URL}/api/issues/search?componentKeys=${sonarProjectKey}&types=VULNERABILITY,BUG,CODE_SMELL&ps=500" \
                                    > ${sonarReportDir}/issues-raw.json
                            """

                            // Récupérer les mesures
                            sh """
                                curl -s -u \${SONAR_AUTH_TOKEN}: \
                                    "\${SONAR_HOST_URL}/api/measures/component?component=${sonarProjectKey}&metricKeys=bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,sqale_index,sqale_rating,reliability_rating,security_rating,ncloc,security_hotspots" \
                                    > ${sonarReportDir}/measures-raw.json
                            """
                            sh """
                                curl -s -u \${SONAR_AUTH_TOKEN}: \
                                    "\${SONAR_HOST_URL}/api/qualitygates/project_status?projectKey=${sonarProjectKey}" \
                                    > ${sonarReportDir}/quality-gate.json
                            """

                            // Fusionner les données
                            sh """
cat > ${sonarReportDir}/merge-sonar.py << EOFPYTHON
import json

sonar_report_dir = '${sonarReportDir}'
sonar_project_key = '${sonarProjectKey}'

with open(f'{sonar_report_dir}/issues-raw.json') as f:
    issues_data = json.load(f)
with open(f'{sonar_report_dir}/measures-raw.json') as f:
    measures_data = json.load(f)
with open(f'{sonar_report_dir}/quality-gate.json') as f:
    quality_gate_data = json.load(f)

quality_gate_status = quality_gate_data.get('projectStatus', {}).get('status', 'UNKNOWN')

merged_report = {
    "projectKey": sonar_project_key,
    "projectName": "Babyfoot Backend",
    "status": quality_gate_status,
    "summary": {},
    "total_issues": issues_data.get('total', 0),
    "detailed_issues": issues_data.get('issues', []),
    "global_measures": measures_data.get('component', {}).get('measures', [])
}

with open('${sonarReportDir}/sonarqube-backend-raw.json', 'w') as f:
    json.dump(merged_report, f, indent=2)

print(f" Rapport SonarQube fusionné !!!")
EOFPYTHON

python3 ${sonarReportDir}/merge-sonar.py
rm -f ${sonarReportDir}/issues-raw.json ${sonarReportDir}/measures-raw.json ${sonarReportDir}/quality-gate.json ${sonarReportDir}/merge-sonar.py
                            """

                            // Métadonnées
                            def metadataJson = JsonOutput.toJson([
                                tool: "sonarqube",
                                service: "backend",
                                build_id: BUILD_NUMBER,
                                scan_type: "sast",
                                scan_start_time: sonarScanStart,
                                scan_end_time: sonarScanEnd,
                                code_introduction_time: env.CODE_INTRODUCTION_TIME.toLong(),
                                git_commit: env.GIT_COMMIT_HASH,
                                git_branch: env.GIT_BRANCH,
                                git_author: env.GIT_AUTHOR,
                                environment: "dev"
                            ])

                            writeFile file: "${sonarReportDir}/metadata.json", text: metadataJson

                            // Normalisation
                            echo "Normalisation du rapport SonarQube Backend..."
                            sh """
                                METADATA_CONTENT=\$(cat ${sonarReportDir}/metadata.json)
                                python3 /usr/local/bin/normalize-reports.py \
                                    ${sonarReportDir}/sonarqube-backend-raw.json \
                                    ${sonarReportDir}/sonarqube-backend-normalized.json \
                                    sonarqube \
                                    "\$METADATA_CONTENT"

                                python3 /usr/local/bin/split_reports.py \
                                     ${sonarReportDir}/sonarqube-backend-normalized.json \
                                     ${sonarReportDir}/sonarqube-backend-split.ndjson
                            """

                            sh "rm -f ${sonarReportDir}/sonarqube-backend-raw.json ${sonarReportDir}/metadata.json"
                        }

                        // ========== SNYK BACKEND ==========
                        echo "\nAnalyse Snyk Backend..."
                        def snykReportDir = "${REPORTS_DIR}/build-${BUILD_NUMBER}/snyk/scans"
                        sh "mkdir -p ${snykReportDir}"

                        sh "snyk auth ${SNYK_TOKEN}"

                        // Scan Maven
                        echo "Snyk Maven scan..."
                        def snykMavenStart = System.currentTimeMillis()
                        sh """
                            snyk test \
                                --maven-project=pom.xml \
                                --severity-threshold=high \
                                --json \
                                > ${snykReportDir}/snyk-backend-maven-raw.json || true

                            snyk-to-html \
                                -i ${snykReportDir}/snyk-backend-maven-raw.json \
                                -o ${snykReportDir}/snyk-backend-maven.html || true
                        """
                        def snykMavenEnd = System.currentTimeMillis()

                        def snykMavenMetadata = JsonOutput.toJson([
                            tool: "snyk",
                            service: "backend",
                            build_id: BUILD_NUMBER,
                            scan_type: "maven",
                            scan_start_time: snykMavenStart,
                            scan_end_time: snykMavenEnd,
                            code_introduction_time: env.CODE_INTRODUCTION_TIME.toLong(),
                            git_commit: env.GIT_COMMIT_HASH,
                            git_branch: env.GIT_BRANCH,
                            git_author: env.GIT_AUTHOR,
                            environment: "dev"
                        ])

                        writeFile file: "${snykReportDir}/maven-metadata.json", text: snykMavenMetadata

                        sh """
                            METADATA_CONTENT=\$(cat ${snykReportDir}/maven-metadata.json)
                            python3 /usr/local/bin/normalize-reports.py \
                                ${snykReportDir}/snyk-backend-maven-raw.json \
                                ${snykReportDir}/snyk-backend-maven-normalized.json \
                                snyk \
                                "\$METADATA_CONTENT"

                            python3 /usr/local/bin/split_reports.py \
                                 ${snykReportDir}/snyk-backend-maven-normalized.json \
                                 ${snykReportDir}/snyk-backend-maven-split.ndjson
                        """

                        // Scan Code
                        echo "Snyk Code scan..."
                        def snykCodeStart = System.currentTimeMillis()
                        sh """
                            snyk code test \
                                --path=. \
                                --severity-threshold=high \
                                --json \
                                > ${snykReportDir}/snyk-backend-code-raw.json || true

                            snyk-to-html \
                                -i ${snykReportDir}/snyk-backend-code-raw.json \
                                -o ${snykReportDir}/snyk-backend-code.html || true
                        """
                        def snykCodeEnd = System.currentTimeMillis()

                        def snykCodeMetadata = JsonOutput.toJson([
                            tool: "snyk",
                            service: "backend",
                            build_id: BUILD_NUMBER,
                            scan_type: "code",
                            scan_start_time: snykCodeStart,
                            scan_end_time: snykCodeEnd,
                            code_introduction_time: env.CODE_INTRODUCTION_TIME.toLong(),
                            git_commit: env.GIT_COMMIT_HASH,
                            git_branch: env.GIT_BRANCH,
                            git_author: env.GIT_AUTHOR,
                            environment: "dev"
                        ])

                        writeFile file: "${snykReportDir}/code-metadata.json", text: snykCodeMetadata

                        sh """
                            METADATA_CONTENT=\$(cat ${snykReportDir}/code-metadata.json)
                            python3 /usr/local/bin/normalize-reports.py \
                                ${snykReportDir}/snyk-backend-code-raw.json \
                                ${snykReportDir}/snyk-backend-code-normalized.json \
                                snyk \
                                "\$METADATA_CONTENT"

                            python3 /usr/local/bin/split_reports.py \
                                 ${snykReportDir}/snyk-backend-code-normalized.json \
                                 ${snykReportDir}/snyk-backend-code-split.ndjson
                        """

                        sh "rm -f ${snykReportDir}/*-raw.json ${snykReportDir}/*-metadata.json"

                        echo "Backend: SonarQube + Snyk terminés et normalisés"
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: "${REPORTS_DIR}/build-${BUILD_NUMBER}/**/*backend*.json", allowEmptyArchive: true
                    archiveArtifacts artifacts: "${REPORTS_DIR}/build-${BUILD_NUMBER}/**/*backend*.html", allowEmptyArchive: true
                }
            }
        }

        stage('Build & SAST Frontend') {
            steps {
                script {
                    echo " ÉTAPE 3: Build et Analyse Frontend "

                    dir('BabyFOOT/frontend') {
                        echo "Installation npm..."
                        sh 'npm install'

                        // ========== SONARQUBE FRONTEND ==========
                        echo "\nAnalyse SonarQube Frontend..."
                        def sonarProjectKey = "babyfoot-frontend"
                        def sonarReportDir = "${REPORTS_DIR}/build-${BUILD_NUMBER}/sonarqube/scans"
                        def sonarScanStart = System.currentTimeMillis()

                        withSonarQubeEnv('SonarQube') {
                            sh "mkdir -p ${sonarReportDir}"

                            sh """
                                sonar-scanner \
                                    -Dsonar.projectKey=${sonarProjectKey} \
                                    -Dsonar.projectName="Babyfoot Frontend" \
                                    -Dsonar.sources=src \
                                    -Dsonar.javascript.ts.jsx.file.suffixes=.js,.jsx,.ts,.tsx
                            """

                            echo "Attente du traitement SonarQube (45s)..."
                            sleep(45)
                            def sonarScanEnd = System.currentTimeMillis()

                            sh """
                                curl -s -u \${SONAR_AUTH_TOKEN}: \
                                    "\${SONAR_HOST_URL}/api/issues/search?componentKeys=${sonarProjectKey}&types=VULNERABILITY,BUG,CODE_SMELL&ps=500" \
                                    > ${sonarReportDir}/issues-raw-front.json
                            """

                            sh """
                                curl -s -u \${SONAR_AUTH_TOKEN}: \
                                    "\${SONAR_HOST_URL}/api/measures/component?component=${sonarProjectKey}&metricKeys=bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,sqale_index,sqale_rating,reliability_rating,security_rating,ncloc,security_hotspots" \
                                    > ${sonarReportDir}/measures-raw-front.json
                            """
                            sh """
                                curl -s -u \${SONAR_AUTH_TOKEN}: \
                                    "\${SONAR_HOST_URL}/api/qualitygates/project_status?projectKey=${sonarProjectKey}" \
                                    > ${sonarReportDir}/quality-gate.json
                            """

                            // Fusion (même script que backend)
                            sh """
cat > ${sonarReportDir}/merge-sonar-front.py << 'EOFPYTHON'
import json

sonar_report_dir = '${sonarReportDir}'
sonar_project_key = '${sonarProjectKey}'

with open(f'{sonar_report_dir}/issues-raw-front.json') as f:
    issues_data = json.load(f)
with open(f'{sonar_report_dir}/measures-raw-front.json') as f:
    measures_data = json.load(f)
with open(f'{sonar_report_dir}/quality-gate.json') as f:
    quality_gate_data = json.load(f)

quality_gate_status = quality_gate_data.get('projectStatus', {}).get('status', 'UNKNOWN')

merged_report = {
    "projectKey": sonar_project_key,
    "projectName": "Babyfoot Frontend",
    "status": quality_gate_status,
    "summary": {},
    "total_issues": issues_data.get('total', 0),
    "detailed_issues": issues_data.get('issues', []),
    "global_measures": measures_data.get('component', {}).get('measures', [])
}

with open('${sonarReportDir}/sonarqube-frontend-raw.json', 'w') as f:
    json.dump(merged_report, f, indent=2)

print(f" Rapport SonarQube fusionné avec succès")
EOFPYTHON

python3 ${sonarReportDir}/merge-sonar-front.py
rm -f ${sonarReportDir}/*-raw-front.json ${sonarReportDir}/quality-gate.json ${sonarReportDir}/merge-sonar-front.py
                            """

                            // Métadonnées
                            def sonarMetadata = JsonOutput.toJson([
                                tool: "sonarqube",
                                service: "frontend",
                                build_id: BUILD_NUMBER,
                                scan_type: "sast",
                                scan_start_time: sonarScanStart,
                                scan_end_time: sonarScanEnd,
                                code_introduction_time: env.CODE_INTRODUCTION_TIME.toLong(),
                                git_commit: env.GIT_COMMIT_HASH,
                                git_branch: env.GIT_BRANCH,
                                git_author: env.GIT_AUTHOR,
                                environment: "dev"
                            ])

                            writeFile file: "${sonarReportDir}/metadata-front.json", text: sonarMetadata

                            sh """
                                METADATA_CONTENT=\$(cat ${sonarReportDir}/metadata-front.json)
                                python3 /usr/local/bin/normalize-reports.py \
                                    ${sonarReportDir}/sonarqube-frontend-raw.json \
                                    ${sonarReportDir}/sonarqube-frontend-normalized.json \
                                    sonarqube \
                                    "\$METADATA_CONTENT"

                                python3 /usr/local/bin/split_reports.py \
                                     ${sonarReportDir}/sonarqube-frontend-normalized.json \
                                     ${sonarReportDir}/sonarqube-frontend-split.ndjson
                            """

                            sh "rm -f ${sonarReportDir}/sonarqube-frontend-raw.json ${sonarReportDir}/metadata-front.json"
                        }

                        // SNYK FRONTEND
                        echo "\nAnalyse Snyk Frontend..."
                        def snykReportDir = "${REPORTS_DIR}/build-${BUILD_NUMBER}/snyk/scans"

                        sh "snyk auth ${SNYK_TOKEN}"

                        // Scan npm
                        def snykNpmStart = System.currentTimeMillis()
                        sh """
                            snyk test \
                                --severity-threshold=high \
                                --json \
                                > ${snykReportDir}/snyk-frontend-npm-raw.json || true

                            snyk-to-html \
                                -i ${snykReportDir}/snyk-frontend-npm-raw.json \
                                -o ${snykReportDir}/snyk-frontend-npm.html || true
                        """
                        def snykNpmEnd = System.currentTimeMillis()

                        def snykNpmMetadata = JsonOutput.toJson([
                            tool: "snyk",
                            service: "frontend",
                            build_id: BUILD_NUMBER,
                            scan_type: "npm",
                            scan_start_time: snykNpmStart,
                            scan_end_time: snykNpmEnd,
                            code_introduction_time: env.CODE_INTRODUCTION_TIME.toLong(),
                            git_commit: env.GIT_COMMIT_HASH,
                            git_branch: env.GIT_BRANCH,
                            git_author: env.GIT_AUTHOR,
                            environment: "dev"
                        ])

                        writeFile file: "${snykReportDir}/npm-metadata.json", text: snykNpmMetadata

                        sh """
                            METADATA_CONTENT=\$(cat ${snykReportDir}/npm-metadata.json)
                            python3 /usr/local/bin/normalize-reports.py \
                                ${snykReportDir}/snyk-frontend-npm-raw.json \
                                ${snykReportDir}/snyk-frontend-npm-normalized.json \
                                snyk \
                                "\$METADATA_CONTENT"

                            python3 /usr/local/bin/split_reports.py \
                                 ${snykReportDir}/snyk-frontend-npm-normalized.json \
                                 ${snykReportDir}/snyk-frontend-npm-split.ndjson
                        """

                        // Scan Code
                        def snykCodeStart = System.currentTimeMillis()
                        sh """
                            snyk code test \
                                --path=. \
                                --severity-threshold=high \
                                --json \
                                > ${snykReportDir}/snyk-frontend-code-raw.json || true

                            snyk-to-html \
                                -i ${snykReportDir}/snyk-frontend-code-raw.json \
                                -o ${snykReportDir}/snyk-frontend-code.html || true
                        """
                        def snykCodeEnd = System.currentTimeMillis()

                        def snykCodeMetadata = JsonOutput.toJson([
                            tool: "snyk",
                            service: "frontend",
                            build_id: BUILD_NUMBER,
                            scan_type: "code",
                            scan_start_time: snykCodeStart,
                            scan_end_time: snykCodeEnd,
                            code_introduction_time: env.CODE_INTRODUCTION_TIME.toLong(),
                            git_commit: env.GIT_COMMIT_HASH,
                            git_branch: env.GIT_BRANCH,
                            git_author: env.GIT_AUTHOR,
                            environment: "dev"
                        ])

                        writeFile file: "${snykReportDir}/code-metadata-front.json", text: snykCodeMetadata

                        sh """
                            METADATA_CONTENT=\$(cat ${snykReportDir}/code-metadata-front.json)
                            python3 /usr/local/bin/normalize-reports.py \
                                ${snykReportDir}/snyk-frontend-code-raw.json \
                                ${snykReportDir}/snyk-frontend-code-normalized.json \
                                snyk \
                                "\$METADATA_CONTENT"

                            python3 /usr/local/bin/split_reports.py \
                                 ${snykReportDir}/snyk-frontend-code-normalized.json \
                                 ${snykReportDir}/snyk-frontend-code-split.ndjson
                        """

                        sh "rm -f ${snykReportDir}/*-raw.json ${snykReportDir}/*-metadata*.json"

                        echo "Frontend: SonarQube + Snyk terminés et normalisés"
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: "${REPORTS_DIR}/build-${BUILD_NUMBER}/**/*frontend*.json", allowEmptyArchive: true
                    archiveArtifacts artifacts: "${REPORTS_DIR}/build-${BUILD_NUMBER}/**/*frontend*.html", allowEmptyArchive: true
                }
            }
        }

        stage('Containerization') {
            steps {
                script {
                    echo " ÉTAPE 4: Construction des images Docker"

                    withCredentials([usernamePassword(
                        credentialsId: 'docker-registry-credentials',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )]) {
                        sh """
                            echo "${DOCKER_PASSWORD}" | docker login ${DOCKER_REGISTRY} --username ${DOCKER_USER} --password-stdin
                        """

                        // Build Backend
                        dir('BabyFOOT/backend') {
                            echo "Build image Backend..."
                            sh """
                                docker build \
                                    --no-cache \
                                    --pull \
                                    -t ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_BACKEND}:${IMAGE_TAG} \
                                    .
                            """
                        }

                        // Build Frontend
                        dir('BabyFOOT/frontend') {
                            echo "Build image Frontend..."
                            sh """
                                docker build \
                                    --no-cache \
                                    --pull \
                                    -t ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_FRONTEND}:${IMAGE_TAG} \
                                    .
                            """
                        }

                        echo "Images Docker construites!!!"
                    }
                }
            }
        }


        stage('Security Scan Images (Trivy)') {
            steps {
                script {
                    echo " ÉTAPE 5: Scan de sécurité des images Docker"

                    def trivyReportDir = "${REPORTS_DIR}/build-${BUILD_NUMBER}/trivy/scans"
                    sh "mkdir -p ${trivyReportDir}"

                    withCredentials([usernamePassword(
                        credentialsId: 'docker-registry-credentials',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )]) {

                        // Scan Backend
                        echo "Trivy scan Backend image..."
                        def trivyBackendStart = System.currentTimeMillis()

                        sh """
                            docker exec trivy trivy image \
                                --format json \
                                --output /shared/build-${BUILD_NUMBER}/trivy/scans/trivy-backend-raw.json \
                                ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_BACKEND}:${IMAGE_TAG} || true
                        """
                        def trivyBackendEnd = System.currentTimeMillis()

                        def trivyBackendMetadata = JsonOutput.toJson([
                            tool: "trivy",
                            service: "backend",
                            build_id: BUILD_NUMBER,
                            scan_type: "container",
                            scan_start_time: trivyBackendStart,
                            scan_end_time: trivyBackendEnd,
                           code_introduction_time: env.CODE_INTRODUCTION_TIME.toLong(),
                             git_commit: env.GIT_COMMIT_HASH,
                            git_branch: env.GIT_BRANCH,
                            git_author: env.GIT_AUTHOR,
                            environment: "dev"
                        ])

                        writeFile file: "${trivyReportDir}/backend-metadata.json", text: trivyBackendMetadata

                        sh """
                            METADATA_CONTENT=\$(cat ${trivyReportDir}/backend-metadata.json)
                            python3 /usr/local/bin/normalize-reports.py \
                                ${trivyReportDir}/trivy-backend-raw.json \
                                ${trivyReportDir}/trivy-backend-normalized.json \
                                trivy \
                                "\$METADATA_CONTENT"

                            python3 /usr/local/bin/split_reports.py \
                                 ${trivyReportDir}/trivy-backend-normalized.json \
                                 ${trivyReportDir}/trivy-backend-split.ndjson
                        """

                        // Scan Frontend
                        echo "Trivy scan Frontend image..."
                        def trivyFrontendStart = System.currentTimeMillis()

                        sh """
                            docker exec trivy trivy image \
                                --format json \
                                --output /shared/build-${BUILD_NUMBER}/trivy/scans/trivy-frontend-raw.json \
                                ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_FRONTEND}:${IMAGE_TAG} || true
                        """
                        def trivyFrontendEnd = System.currentTimeMillis()

                        def trivyFrontendMetadata = JsonOutput.toJson([
                            tool: "trivy",
                            service: "frontend",
                            build_id: BUILD_NUMBER,
                            scan_type: "container",
                            scan_start_time: trivyFrontendStart,
                            scan_end_time: trivyFrontendEnd,
                            code_introduction_time: env.CODE_INTRODUCTION_TIME.toLong(),
                            git_commit: env.GIT_COMMIT_HASH,
                            git_branch: env.GIT_BRANCH,
                            git_author: env.GIT_AUTHOR,
                            environment: "dev"
                        ])

                        writeFile file: "${trivyReportDir}/frontend-metadata.json", text: trivyFrontendMetadata

                        sh """
                            METADATA_CONTENT=\$(cat ${trivyReportDir}/frontend-metadata.json)
                            python3 /usr/local/bin/normalize-reports.py \
                                ${trivyReportDir}/trivy-frontend-raw.json \
                                ${trivyReportDir}/trivy-frontend-normalized.json \
                                trivy \
                                "\$METADATA_CONTENT"

                            python3 /usr/local/bin/split_reports.py \
                                 ${trivyReportDir}/trivy-frontend-normalized.json \
                                 ${trivyReportDir}/trivy-frontend-split.ndjson

                        """

                        sh "rm -f ${trivyReportDir}/*-raw.json ${trivyReportDir}/*-metadata.json"

                        echo "Trivy scans terminés et normalisés"
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: "${REPORTS_DIR}/build-${BUILD_NUMBER}/trivy/**/*.json", allowEmptyArchive: true
                }
            }
        }

        stage('Trigger Watcher Alerte') {
            steps {
                script {
                    echo "ETAPE FINALE : Déclenchement de l'alerte de résolution MTTR..."
                    withCredentials([usernamePassword(
                        credentialsId: 'elastic-credentials',
                        usernameVariable: 'ELASTIC_USER',
                        passwordVariable: 'ELASTIC_PASS'
                    )]) {
                        sh """
                            curl -X POST "http://elasticsearch:9200/_watcher/watch/watcher_mark_resolved/_execute" -u ${ELASTIC_USER}:${ELASTIC_PASS} -H 'Content-Type: application/json' -d '{}'
                        """
                    }
                }
            }
        }

        stage('Push Docker Images') {
            steps {
                script {
                    echo " ÉTAPE 6: Publication des images Docker"

                    withCredentials([usernamePassword(
                        credentialsId: 'docker-registry-credentials',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )]) {
                        sh """
                            echo "${DOCKER_PASSWORD}" | docker login ${DOCKER_REGISTRY} --username ${DOCKER_USER} --password-stdin

                            # Push avec tag du build
                            docker push ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_BACKEND}:${IMAGE_TAG}
                            docker push ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_FRONTEND}:${IMAGE_TAG}

                            # Tag et push latest
                            docker tag ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_BACKEND}:${IMAGE_TAG} \
                                       ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_BACKEND}:latest
                            docker push ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_BACKEND}:latest

                            docker tag ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_FRONTEND}:${IMAGE_TAG} \
                                       ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_FRONTEND}:latest
                            docker push ${DOCKER_REGISTRY}/${DOCKER_USER}/${IMAGE_NAME_FRONTEND}:latest
                        """

                        echo "Images publiées sur Docker Hub"
                    }
                }
            }
        }

        stage('Deployment') {
            steps {
                script {
                    dir('BabyFOOT'){

                        echo " ÉTAPE 7: Déploiement avec Docker Compose"

                        withCredentials([usernamePassword(
                            credentialsId: 'docker-registry-credentials',
                            usernameVariable: 'DOCKER_USER',
                            passwordVariable: 'DOCKER_PASSWORD'
                        )]) {
                            sh """
                                echo "${DOCKER_PASSWORD}" | docker login ${DOCKER_REGISTRY} --username ${DOCKER_USER} --password-stdin

                                docker-compose pull
                                docker-compose down
                                docker-compose  up -d
                            """

                            echo "Déploiement terminé!!!"
                        }
                    }
                }
            }
        }


    }
}