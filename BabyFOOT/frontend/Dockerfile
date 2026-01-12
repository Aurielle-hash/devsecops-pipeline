###################################
# STAGE 1: LE BUILD DE L'APPLICATION
###################################
# Utilisation d'une image complète pour le build
FROM node:18-alpine AS builder

# Définir le répertoire de travail pour les sources
WORKDIR /app

# Copier uniquement les fichiers de configuration pour maximiser le cache Docker
COPY package*.json ./

# Installer les dépendances
RUN npm install

# Copier tout le code source (y compris le dossier 'public' et 'src')
COPY . .

# Lancer la construction de l'application React
# Cette commande échouait car 'index.html' n'était peut-être pas trouvé dans 'public'
# La copie complète au-dessus devrait corriger cela.
RUN npm run build

###################################
# STAGE 2: L'IMAGE DE PRODUCTION (Légère avec 'serve')
###################################
# Utiliser une image Node Alpine légère pour le runtime
FROM node:18-alpine AS final

# Installer 'serve' globalement dans cette image légère
# Remarque: 'serve' est une dépendance de production légère
RUN npm install -g serve

# Définir le répertoire de travail dans le stage final
WORKDIR /usr/app

# Copier les fichiers de build optimisés du premier stage (builder)
# Seul le répertoire 'build' est nécessaire.
COPY --from=builder /app/build ./build

# Exposer le port pour le service
EXPOSE 3000

# Servir le build de production
CMD ["serve", "-s", "build", "-l", "3000"]
