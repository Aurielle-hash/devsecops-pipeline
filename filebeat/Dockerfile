FROM docker.elastic.co/beats/filebeat:7.17.7

# Copier la config
COPY filebeat.yml /usr/share/filebeat/filebeat.yml

# Fixer les permissions (root reste dispo dans WSL/Docker)
USER root

# Sécuriser le fichier de configuration
# retirer les droits d'écriture pour les autres et le groupe
# et changer le groupe pour filebeat
RUN chmod go-w /usr/share/filebeat/filebeat.yml && \
    chown -R root:filebeat /usr/share/filebeat

#RUN chown root:filebeat /usr/share/filebeat/filebeat.yml

# Revenir à l’utilisateur par défaut
USER filebeat
