# Étape 1 : Construction de l'application
# Utilise une image de base avec Maven et JDK 17
FROM maven:3.9.9-eclipse-temurin-17-focal AS build

# Définit le répertoire de travail
WORKDIR /app

# Copie le pom.xml pour télécharger les dépendances
COPY pom.xml .

# Télécharge les dépendances
RUN mvn dependency:go-offline -B

# Copie le code source
COPY src src

# Construit l'application
RUN mvn clean package -DskipTests

# Étape 2 : Création de l'image finale
# Utilise une image de base plus légère pour l'exécution
FROM eclipse-temurin:17-jre-jammy

# Définit le répertoire de travail
WORKDIR /app

# Copie le fichier JAR construit à partir de l'étape de construction
COPY --from=build /app/target/*.jar app.jar

# Télécharge l'agent APM Elastic
ADD https://repo1.maven.org/maven2/co/elastic/apm/elastic-apm-agent/1.55.1/elastic-apm-agent-1.55.1.jar /elastic-apm-agent.jar

# Expose le port de l'application
EXPOSE 8085

# Commande par défaut pour exécuter l'application
# Note : Cette commande peut être écrasée par docker-compose
CMD ["java", "-jar", "app.jar"]
