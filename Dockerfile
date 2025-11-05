# Multi-stage build for Spring Boot JSP app

FROM maven:3.9.9-eclipse-temurin-17 AS builder
WORKDIR /workspace

# Cache dependencies first
COPY pom.xml .
RUN mvn -B -q -DskipTests dependency:go-offline

# Copy sources and build
COPY src ./src
COPY .mvn ./.mvn
COPY mvnw mvnw
RUN chmod +x mvnw || true
RUN mvn -B -q -DskipTests package

FROM eclipse-temurin:17-jre
WORKDIR /app

# Copy fat jar
COPY --from=builder /workspace/target/jspdemo1-1.0.0.jar app.jar

# Use cloud profile by default; Cloud Run sets PORT env var
ENV SPRING_PROFILES_ACTIVE=cloud
ENV JAVA_OPTS="-Xms256m -Xmx512m"

EXPOSE 8080
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]


