#!/bin/bash

set -e

NAMESPACE="cicd-demo"
APP_NAME="demo-app"
NEW_VERSION=$1
CURRENT_COLOR=$(kubectl get service ${APP_NAME}-service -n ${NAMESPACE} -o jsonpath='{.spec.selector.color}' 2>/dev/null || echo "blue")

if [ "$CURRENT_COLOR" == "blue" ]; then
    NEW_COLOR="green"
else
    NEW_COLOR="blue"
fi

echo "================================================"
echo "  Blue-Green Deployment"
echo "================================================"
echo "Current Color: $CURRENT_COLOR"
echo "New Color: $NEW_COLOR"
echo "New Version: $NEW_VERSION"
echo ""

# Deploy new version with new color
echo "Step 1: Deploying $NEW_COLOR environment with version $NEW_VERSION..."

kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${APP_NAME}-${NEW_COLOR}
  namespace: ${NAMESPACE}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ${APP_NAME}
      color: ${NEW_COLOR}
  template:
    metadata:
      labels:
        app: ${APP_NAME}
        color: ${NEW_COLOR}
        version: ${NEW_VERSION}
    spec:
      containers:
      - name: ${APP_NAME}
        image: cicd-demo-app:${NEW_VERSION}
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
EOF

# Wait for new deployment to be ready
echo "Step 2: Waiting for $NEW_COLOR deployment to be ready..."
kubectl rollout status deployment/${APP_NAME}-${NEW_COLOR} -n ${NAMESPACE}

# Run smoke tests
echo "Step 3: Running smoke tests on $NEW_COLOR environment..."
sleep 10

POD_NAME=$(kubectl get pods -n ${NAMESPACE} -l color=${NEW_COLOR} -o jsonpath='{.items[0].metadata.name}')
HEALTH_STATUS=$(kubectl exec -n ${NAMESPACE} ${POD_NAME} -- curl -s http://localhost:3000/health | jq -r '.status')

if [ "$HEALTH_STATUS" != "healthy" ]; then
    echo "ERROR: Health check failed on $NEW_COLOR environment"
    exit 1
fi

echo "✓ Smoke tests passed"

# Switch traffic to new color
echo "Step 4: Switching traffic to $NEW_COLOR..."

kubectl patch service ${APP_NAME}-service -n ${NAMESPACE} -p "{\"spec\":{\"selector\":{\"app\":\"${APP_NAME}\",\"color\":\"${NEW_COLOR}\"}}}"

echo "✓ Traffic switched to $NEW_COLOR"

# Monitor for 30 seconds
echo "Step 5: Monitoring $NEW_COLOR environment for 30 seconds..."
sleep 30

# Check if everything is stable
ERROR_COUNT=$(kubectl logs -n ${NAMESPACE} -l color=${NEW_COLOR} --tail=100 | grep -i error | wc -l || echo "0")

if [ "$ERROR_COUNT" -gt 5 ]; then
    echo "WARNING: Detected $ERROR_COUNT errors. Rolling back..."
    kubectl patch service ${APP_NAME}-service -n ${NAMESPACE} -p "{\"spec\":{\"selector\":{\"app\":\"${APP_NAME}\",\"color\":\"${CURRENT_COLOR}\"}}}"
    echo "Rolled back to $CURRENT_COLOR"
    exit 1
fi

echo "Step 6: Deployment successful! Cleaning up old $CURRENT_COLOR environment..."
kubectl delete deployment ${APP_NAME}-${CURRENT_COLOR} -n ${NAMESPACE} --ignore-not-found=true

echo ""
echo "================================================"
echo "  Blue-Green Deployment Complete!"
echo "================================================"
echo "Active Color: $NEW_COLOR"
echo "Version: $NEW_VERSION"