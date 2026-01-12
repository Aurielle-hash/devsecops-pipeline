# 🏓 Babyfoot Championship - Application Full-Stack avec Elastic APM

Une application complète de gestion de parties de babyfoot avec un frontend React et un backend Spring Boot, entièrement instrumentée avec Elastic APM pour une observabilité complète.

## 🚀 Fonctionnalités

### Frontend (React)
- ⚽ Création et gestion de matchs en temps réel
- 🏆 Gestion des joueurs avec statistiques
- 📊 Tableau de bord avec historique des parties
- 🎯 Interface responsive et moderne
- 📈 Instrumentation APM JavaScript complète

### Backend (Spring Boot)
- 🔧 API REST complète (CRUD joueurs et matchs)
- 💾 Base de données H2 en mémoire
- 📊 Mise à jour automatique des statistiques
- 🔍 Instrumentation APM Java avec agent
- 🌐 Support CORS pour le frontend

### Observabilité (Elastic Stack)
- 📈 **APM Server** : Collecte des traces et métriques
- 🔍 **Elasticsearch** : Stockage des données d'observabilité
- 📊 **Kibana** : Visualisation et analyse des performances
- 🎯 Traces distribuées entre frontend et backend
- 📱 Monitoring des performances utilisateur (RUM)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │  Spring Boot    │    │  Elastic Stack  │
│   (Port 3000)   │◄──►│   (Port 8085)   │◄──►│                 │
│                 │    │                 │    │ • Elasticsearch │
│ • APM RUM Agent │    │ • APM Java Agent│    │ • Kibana        │
│ • Axios + APM   │    │ • REST APIs     │    │ • APM Server    │
│ • React Router  │    │ • H2 Database   │    │   (Port 8200)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Installation et Démarrage

### Prérequis
- **Windows** : APM Server installé en service, Java 17+, Node.js 18+
- **Docker** : Docker Desktop avec Docker Compose

### Démarrage avec Docker Compose

1. **Cloner le projet**
```bash
git clone <repository-url>
cd babyfoot-app
```

2. **Lancer l'ensemble de la stack**
```bash
docker-compose up -d
docker-compose ps
```

3. **Vérifier que tous les services sont démarrés**
```bash
docker-compose ps
```

### Services disponibles

| Service | URL                   | Description |
|---------|-----------------------|-------------|
| **Frontend** | http://localhost:3000 | Interface React de l'application |
| **Backend** | http://localhost:8085 | API REST Spring Boot |
| **Kibana** | http://localhost:5601 | Interface de visualisation |
| **APM Server** | http://localhost:8200 | Serveur de collecte APM |
| **Elasticsearch** | http://localhost:9200 | Base de données Elastic |

## 📊 Configuration APM

### Frontend (JavaScript)
```javascript
import { init as initApm } from '@elastic/apm-rum'

const apm = initApm({
  serviceName: 'babyfoot-frontend',
  serverUrl: 'http://localhost:8200',
  environment: 'development',
  distributedTracingOrigins: ['http://localhost:8085']
})
```

### Backend (Java)
```bash
java -javaagent:/elastic-apm-agent.jar \
  -Delastic.apm.service_name=babyfoot-backend \
  -Delastic.apm.server_urls=http://localhost:8200 \
  -Delastic.apm.environment=development \
  -Delastic.apm.application_packages=com.babyfoot \
  -jar target/babyfoot-backend.jar
```

## ⚙️ Activation RUM dans APM Server

### 🔹 Sur Windows (APM Server installé en local)

Éditer `apm-server.yml` (exemple : `C:\Program Files\Elastic\APM-Server\config\apm-server.yml`) :

```yaml
apm-server:
  host: "0.0.0.0:8200"
  rum:
    enabled: true
    allow_origins: ["*"]
    event_rate:
      limit: 300
      lru_size: 1000
```


#### Redémarrer le service APM Server :

```bash
net stop apm-server
net start apm-server
```

### 🔹 Sur Docker (APM Server conteneurisé)

Éditer `apm-server.yml` (exemple : `C:\Program Files\Elastic\APM-Server\config\apm-server.yml`) :

```yaml
apm-server:
  image: docker.elastic.co/apm/apm-server:7.17.15
  environment:
    - apm-server.rum.enabled=true
    - apm-server.rum.allow_origins=["*"]
    - apm-server.rum.event_rate.limit=300
    - apm-server.rum.event_rate.lru_size=1000
```
#### Relancer
```bash
docker-compose down apm-server
docker-compose up -d apm-server
```

## 🔗 Liaison Front ↔ Back

- Axios est utilisé pour gérer toutes les requêtes HTTP du frontend → backend (api.js).
- Le backend expose son API sur /api/....
- Exemple : playersAPI.getAll() → GET http://localhost:8085/api/players.
- Grâce à distributedTracingOrigins, les transactions frontend sont corrélées automatiquement avec les transactions backend dans Kibana.

## 🎯 Utilisation

### 1. Créer des joueurs
- Accédez à l'onglet "🏆 Joueurs"
- Ajoutez de nouveaux joueurs
- Consultez leurs statistiques

### 2. Lancer un match
- Allez dans "⚽ Nouveau Match"
- Sélectionnez deux joueurs
- Cliquez sur "Commencer le Match"

### 3. Gérer les scores
- Dans l'onglet "📊 Scores"
- Utilisez les boutons +/- pour mettre à jour les scores
- Terminez le match quand c'est fini

### 4. Analyser les performances
- Ouvrez Kibana : http://localhost:5601
- Allez dans "Observability" → "APM"
- Explorez les services `babyfoot-frontend` et `babyfoot-backend`

## 📈 Métriques APM Collectées

### Frontend
- ⏱️ **Page Load Times** : Temps de chargement des pages
- 🔄 **AJAX Requests** : Appels API vers le backend
- 🖱️ **User Interactions** : Clics, navigation
- ❌ **JavaScript Errors** : Erreurs côté client
- 📱 **Real User Monitoring** : Expérience utilisateur réelle

### Backend
- 🌐 **HTTP Requests** : Toutes les requêtes REST
- 💾 **Database Queries** : Requêtes JPA/Hibernate
- ⚡ **Method Tracing** : Performance des méthodes
- 🔗 **Distributed Tracing** : Corrélation frontend/backend
- 📊 **JVM Metrics** : Mémoire, GC, threads

## 🔧 Développement Local

### Backend
```bash
cd backend
./mvnw spring-boot:run
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## 🐳 Structure Docker

```
babyfoot-app/
├── backend/
│   ├── Dockerfile
│   └── src/main/java/com/babyfoot/
├── frontend/
│   ├── Dockerfile
│   └── src/
├── docker-compose.yml
└── README.md
```

## 📝 API Endpoints

### Joueurs
- `GET /api/players` - Liste tous les joueurs
- `POST /api/players` - Crée un nouveau joueur
- `GET /api/players/{id}` - Récupère un joueur par ID
- `PUT /api/players/{id}` - Met à jour un joueur
- `DELETE /api/players/{id}` - Supprime un joueur

### Matchs
- `GET /api/matches` - Liste tous les matchs
- `POST /api/matches` - Crée un nouveau match
- `GET /api/matches/active` - Matchs en cours
- `PUT /api/matches/{id}/score` - Met à jour le score
- `PUT /api/matches/{id}/finish` - Termine un match
- `DELETE /api/matches/{id}` - Supprime un match

## 🎨 Fonctionnalités Avancées

- 🔄 **Temps réel** : Mise à jour automatique des scores
- 📊 **Statistiques** : Calcul automatique des victoires/défaites
- 🎯 **Validation** : Contrôles de saisie robustes
- 📱 **Responsive** : Interface adaptée mobile/desktop
- 🔍 **Observabilité** : Traces complètes dans Kibana
- ⚡ **Performance** : Optimisations frontend/backend

## 🚀 Déploiement Production

Pour un déploiement en production, modifiez :

1. **Variables d'environnement APM**
2. **Configuration de sécurité Elasticsearch**
3. **Certificats SSL/TLS**
4. **Configuration réseau Docker**
5. **Persistence des données**

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature
3. Committez vos changements
4. Poussez vers la branche
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

**🎯 Objectif atteint** : Application full-stack complètement instrumentée avec Elastic APM, prête pour l'analyse de performance dans Kibana ! 🚀