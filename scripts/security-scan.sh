#!/bin/bash

set -e

IMAGE_NAME=${1:-cicd-demo-app:latest}
SEVERITY=${2:-HIGH,CRITICAL}
OUTPUT_FORMAT=${3:-table}

echo "=========================================="
echo "  Container Security Scanning with Trivy"
echo "=========================================="
echo "Image: $IMAGE_NAME"
echo "Severity: $SEVERITY"
echo ""

# Create reports directory
mkdir -p reports/security

# Scan for vulnerabilities
echo "Scanning for vulnerabilities..."
trivy image \
  --severity $SEVERITY \
  --format $OUTPUT_FORMAT \
  --output reports/security/trivy-report.txt \
  $IMAGE_NAME

# Scan for misconfigurations
echo ""
echo "Scanning for misconfigurations..."
trivy config \
  --severity $SEVERITY \
  ./app/Dockerfile

# Generate JSON report for CI/CD integration
echo ""
echo "Generating JSON report..."
trivy image \
  --severity $SEVERITY \
  --format json \
  --output reports/security/trivy-report.json \
  $IMAGE_NAME

# Check if critical vulnerabilities exist
CRITICAL_COUNT=$(trivy image --severity CRITICAL --format json $IMAGE_NAME 2>/dev/null | jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length')

echo ""
echo "=========================================="
echo "Scan Results:"
echo "Critical Vulnerabilities: $CRITICAL_COUNT"
echo "Full report: reports/security/trivy-report.txt"
echo "=========================================="

# Fail if critical vulnerabilities found
if [ "$CRITICAL_COUNT" -gt 0 ]; then
    echo "ERROR: Critical vulnerabilities found!"
    exit 1
fi

echo "Security scan passed!"
exit 0