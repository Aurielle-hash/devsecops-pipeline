#!/bin/bash

echo "📋 Logs de l'application Babyfoot"
echo "================================"

if [ "$1" = "frontend" ]; then
    echo "📱 Logs du Frontend React:"
    docker-compose logs -f babyfoot-frontend
elif [ "$1" = "backend" ]; then
    echo "⚙️ Logs du Backend Spring Boot:"
    docker-compose logs -f babyfoot-backend
elif [ "$1" = "apm" ]; then
    echo "📊 Logs d'APM Server:"
    docker-compose logs -f babyfoot-apm-server
elif [ "$1" = "elasticsearch" ]; then
    echo "🔍 Logs d'Elasticsearch:"
    docker-compose logs -f babyfoot-elasticsearch
elif [ "$1" = "kibana" ]; then
    echo "📈 Logs de Kibana:"
    docker-compose logs -f babyfoot-kibana
else
    echo "Usage: ./logs.sh [service]"
    echo ""
    echo "Services disponibles:"
    echo "  frontend      - Logs du frontend React"
    echo "  backend       - Logs du backend Spring Boot"
    echo "  apm          - Logs d'APM Server"
    echo "  elasticsearch - Logs d'Elasticsearch"
    echo "  kibana       - Logs de Kibana"
    echo ""
    echo "Ou voir tous les logs:"
    docker-compose logs -f
fi