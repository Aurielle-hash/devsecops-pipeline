FROM docker.elastic.co/beats/metricbeat:7.17.7

# Copier la config Metricbeat
COPY metricbeat.yml /usr/share/metricbeat/metricbeat.yml

# Fixer les permissions
USER root
RUN chmod go-w /usr/share/metricbeat/metricbeat.yml && \
    chown root:metricbeat /usr/share/metricbeat/metricbeat.yml

# Revenir à l’utilisateur par défaut
USER metricbeat
