#!/bin/bash

echo "Starting SonarQube analysis..."
sonar-scanner \
  -Dsonar.projectKey=scripts-python \
  -Dsonar.sources=/usr/src/src \
  -Dsonar.host.url=http://sonarqube:9000 \
  -Dsonar.login=sqp_... # Placeholder for SonarQube token, user needs to replace this

echo "Starting OWASP Dependency-Check analysis..."
/opt/dependency-check/bin/dependency-check.sh \
  --project "scripts-python" \
  --scan /usr/src \
  --format HTML \
  --out /usr/src/owasp-report \
  --enableExperimental \
  --enableRetired

echo "Analysis complete."
