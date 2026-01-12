# 🚀 Guide de Déploiement - Application Babyfoot

## 📋 Prérequis

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB d'espace disque libre

## 🏗️ Architecture de Déploiement

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │  Spring Boot    │    │  Elastic Stack  │
│   (Port 3000)   │◄──►│   (Port 8080)   │◄──►│                 │
│                 │    │                 │    │ • Elasticsearch │
│ • APM RUM Agent │    │ • APM Java Agent│    │ • Kibana        │
│ • Axios + APM   │    │ • REST APIs     │    │ • APM Server    │
│ • React Router  │    │ • H2 Database   │    │   (Port 8200)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Déploiement Rapide

### 1. Cloner le Projet

```bash
git clone <repository-url>
cd babyfoot-app
```

### 2. Démarrage Automatique

```bash
# Démarrer l'application complète
./start-app.sh

# Ou manuellement
docker-compose up --build -d
```

### 3. Vérification

```bash
# Vérifier le statut des services
docker-compose ps

# Voir les logs
./logs.sh
```

## 🔧 Configuration Avancée

### Variables d'Environnement

Créer un fichier `.env` pour personnaliser la configuration :

```bash
# Frontend
REACT_APP_BACKEND_URL=http://localhost:8080
REACT_APP_APM_SERVER_URL=http://localhost:8200

# Backend
SPRING_PROFILES_ACTIVE=docker
SERVER_PORT=8080

# Elastic Stack
ELASTICSEARCH_HEAP_SIZE=512m
KIBANA_ELASTICSEARCH_HOSTS=http://elasticsearch:9200
APM_SERVER_HOST=0.0.0.0:8200
```

### Personnalisation APM

#### Frontend (React)
```javascript
// src/apm.js
export const apm = initApm({
  serviceName: 'babyfoot-frontend',
  serverUrl: 'http://localhost:8200',
  environment: 'production', // Changer selon l'environnement
  distributedTracingOrigins: ['http://localhost:8080'],
  capturePageLoad: true,
  debug: false // Désactiver en production
})
```

#### Backend (Java)
```bash
# Variables d'environnement pour le conteneur backend
-Delastic.apm.service_name=babyfoot-backend
-Delastic.apm.server_urls=http://apm-server:8200
-Delastic.apm.environment=production
-Delastic.apm.application_packages=com.babyfoot
-Delastic.apm.log_level=WARN
```

## 📊 Monitoring et Observabilité

### Accès aux Services

| Service | URL | Description |
|---------|-----|-------------|
| **Application** | http://localhost:3000 | Interface utilisateur |
| **API Backend** | http://localhost:8080 | API REST |
| **Kibana** | http://localhost:5601 | Dashboard APM |
| **APM Server** | http://localhost:8200 | Collecteur de traces |
| **Elasticsearch** | http://localhost:9200 | Base de données |

### Configuration Kibana

1. **Première connexion** : http://localhost:5601
2. **Navigation** : Observability → APM
3. **Services disponibles** :
    - `babyfoot-frontend` (React)
    - `babyfoot-backend` (Spring Boot)

### Métriques Collectées

#### Frontend
- ⏱️ Page Load Times
- 🔄 AJAX Requests
- 🖱️ User Interactions
- ❌ JavaScript Errors
- 📱 Real User Monitoring

#### Backend
- 🌐 HTTP Requests
- 💾 Database Queries
- ⚡ Method Tracing
- 🔗 Distributed Tracing
- 📊 JVM Metrics

## 🛠️ Développement Local

### Backend Seul

```bash
cd backend
./mvnw spring-boot:run
```

### Frontend Seul

```bash
cd frontend
npm install
npm start
```

### Base de Données H2

- **Console** : http://localhost:8080/h2-console
- **JDBC URL** : `jdbc:h2:mem:babyfoot`
- **Username** : `sa`
- **Password** : (vide)

## 🐛 Dépannage

### Problèmes Courants

#### Services ne démarrent pas
```bash
# Vérifier les logs
./logs.sh

# Redémarrer les services
docker-compose restart
```

#### Elasticsearch ne démarre pas
```bash
# Augmenter la mémoire virtuelle (Linux)
sudo sysctl -w vm.max_map_count=262144

# Ou dans docker-compose.yml
ulimits:
  memlock:
    soft: -1
    hard: -1
```

#### APM ne reçoit pas de données
```bash
# Vérifier la connectivité
curl http://localhost:8200

# Vérifier les logs APM
./logs.sh apm
```

### Commandes Utiles

```bash
# Voir l'utilisation des ressources
docker stats

# Nettoyer les conteneurs
docker-compose down --volumes --remove-orphans

# Reconstruire complètement
docker-compose build --no-cache

# Voir les logs en temps réel
docker-compose logs -f [service-name]
```

## 🔒 Sécurité

### Production

1. **Activer l'authentification Elasticsearch**
2. **Configurer HTTPS**
3. **Utiliser des secrets Docker**
4. **Limiter l'exposition des ports**

### Variables Sensibles

```bash
# Utiliser Docker secrets
echo "mon-secret" | docker secret create elastic-password -
```

## 📈 Performance

### Optimisations

1. **Elasticsearch** : Ajuster la heap size selon la RAM
2. **APM Server** : Configurer le sampling rate
3. **Frontend** : Activer la compression gzip
4. **Backend** : Optimiser les requêtes JPA

### Monitoring des Ressources

```bash
# Utilisation mémoire
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Espace disque
docker system df
```

## 🔄 Mise à Jour

### Versions Elastic Stack

```bash
# Modifier docker-compose.yml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# Redéployer
docker-compose up -d
```

### Application

```bash
# Reconstruire après modifications
docker-compose build
docker-compose up -d
```

## 📝 Logs et Debugging

### Niveaux de Log

- **Frontend** : Console du navigateur + APM
- **Backend** : Logs Spring Boot + APM traces
- **APM Server** : Logs de collecte
- **Elasticsearch** : Logs d'indexation

### Export des Données

```bash
# Backup Elasticsearch
docker exec babyfoot-elasticsearch \
  curl -X GET "localhost:9200/_snapshot"
```

---

**🎯 L'application est maintenant prête pour la production avec une observabilité complète !** 🚀