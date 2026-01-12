#!/bin/bash

echo "🏓 Démarrage de l'application Babyfoot avec Elastic APM"
echo "=================================================="

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez installer Docker pour continuer."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez installer Docker Compose pour continuer."
    exit 1
fi

echo "✅ Docker et Docker Compose sont installés"

# Arrêter les conteneurs existants
echo "🛑 Arrêt des conteneurs existants..."
docker-compose down

# Construire et démarrer tous les services
echo "🚀 Construction et démarrage des services..."
docker-compose up --build -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 30

# Vérifier le statut des services
echo "📊 Vérification du statut des services..."
docker-compose ps

echo ""
echo "🎉 Application démarrée avec succès !"
echo ""
echo "📱 Services disponibles :"
echo "  • Frontend React:     http://localhost:3000"
echo "  • Backend Spring Boot: http://localhost:8080"
echo "  • Kibana (APM):       http://localhost:5601"
echo "  • APM Server:         http://localhost:8200"
echo "  • Elasticsearch:      http://localhost:9200"
echo ""
echo "🔍 Pour voir les traces APM :"
echo "  1. Ouvrez Kibana: http://localhost:5601"
echo "  2. Allez dans 'Observability' → 'APM'"
echo "  3. Explorez les services 'babyfoot-frontend' et 'babyfoot-backend'"
echo ""
echo "🏓 Amusez-vous bien avec votre application Babyfoot !"