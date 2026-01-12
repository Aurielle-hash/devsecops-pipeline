# 1. Partir de l'image Jenkins officielle
FROM jenkins/jenkins:lts-jdk17

# 2. Passer en utilisateur root pour installer des paquets
USER root

# 3. Installer le client Docker CLI (les "boutons" de notre télécommande)
RUN apt-get update && apt-get install -y curl gnupg
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
RUN chmod a+r /etc/apt/keyrings/docker.gpg
RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update && apt-get install -y docker-ce-cli

# 3.1. Installer Docker Compose (V2) pour le déploiement
# Nous créons d'abord le répertoire cible pour les plugins CLI Docker
RUN mkdir -p /usr/local/lib/docker/cli-plugins

# Télécharge et installe le binaire (toutes les commandes dans la même couche)
RUN DOCKER_COMPOSE_VERSION="2.27.1" && \
    curl -SL https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# On crée un lien symbolique pour la compatibilité avec l'ancienne syntaxe docker-compose (avec tiret)
RUN ln -s /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose


#3.2. Ajouter les scripts de normalisation et d'applatissement (splitting) des rapports
COPY scripts/normalize-reports.py /usr/local/bin/normalize-reports.py
COPY scripts/split_reports.py /usr/local/bin/split_reports.py

RUN chmod +x /usr/local/bin/normalize-reports.py
RUN chmod +x /usr/local/bin/split_reports.py

# 3.3. AJOUT DE PYTHON 3 ET DES DÉPENDANCES POUR LE TRAITEMENT DES RAPPORTS
# Assure que Python3 et pip3 sont installés
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    # Installe la librairie 'requests'. Nous utilisons --break-system-packages
    # pour contourner l'erreur "externally-managed-environment" (PEP 668).
    python3 -m pip install requests --break-system-packages && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# 4. Ajouter le dépôt PHP et installer PHP avec Composer
RUN apt-get install -y apt-transport-https ca-certificates
RUN curl -sSLo /usr/share/keyrings/deb.sury.org-php.gpg https://packages.sury.org/php/apt.gpg
# Correction ici : Remplacement de $(lsb_release -sc) par "bookworm"
RUN echo "deb [signed-by=/usr/share/keyrings/deb.sury.org-php.gpg] https://packages.sury.org/php/ trixie main" | tee /etc/apt/sources.list.d/sury-php.list
RUN apt-get update && apt-get install -y php8.2-cli php8.2-mbstring php8.2-xml php8.2-curl php8.2-zip unzip
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
RUN chmod +x /usr/local/bin/composer

# Donner les droits d’exécution aux binaires
RUN mkdir -p /usr/local/bin/snyk_binaries
COPY snyk_binaries/* /usr/local/bin/snyk_binaries/
RUN chmod +x /usr/local/bin/snyk_binaries/*

# Ajouter un lien symbolique pour que "snyk" et "snyk-to-html" soient accessibles globalement
RUN ln -s /usr/local/bin/snyk_binaries/snyk-linux /usr/local/bin/snyk && \
    ln -s /usr/local/bin/snyk_binaries/snyk-to-html-linux /usr/local/bin/snyk-to-html

# 5. Mettre à jour le truststore pour inclure le certificat GitLab
COPY ./certs/gitlab.crt /usr/local/share/ca-certificates/gitlab.crt
RUN update-ca-certificates

# 6. Ajouter l'utilisateur 'jenkins' au groupe 'root' (qui a le GID 0)
RUN usermod -aG root jenkins

# 7. Revenir à l'utilisateur jenkins par défaut pour la sécurité
USER jenkins
