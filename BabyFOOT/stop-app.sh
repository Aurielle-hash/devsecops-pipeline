#!/bin/bash

echo "🛑 Arrêt de l'application Babyfoot"
echo "================================="

# Arrêter tous les conteneurs
docker-compose down

# Nettoyer les volumes (optionnel)
read -p "Voulez-vous supprimer les données Elasticsearch ? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️ Suppression des volumes..."
    docker-compose down -v
    docker volume prune -f
fi

echo "✅ Application arrêtée avec succès"