#!/bin/bash

set -e

echo "=========================================="
echo "  Dependency Vulnerability Scanning"
echo "=========================================="

cd app

# Create reports directory
mkdir -p ../reports/dependencies

# Run npm audit
echo "Running npm audit..."
npm audit --json > ../reports/dependencies/npm-audit.json || true
npm audit > ../reports/dependencies/npm-audit.txt || true

# Check for high/critical vulnerabilities
HIGH_VULNS=$(npm audit --json 2>/dev/null | jq '.metadata.vulnerabilities.high // 0')
CRITICAL_VULNS=$(npm audit --json 2>/dev/null | jq '.metadata.vulnerabilities.critical // 0')

echo ""
echo "=========================================="
echo "Vulnerability Summary:"
echo "High: $HIGH_VULNS"
echo "Critical: $CRITICAL_VULNS"
echo "=========================================="

# Fail if critical vulnerabilities found
if [ "$CRITICAL_VULNS" -gt 0 ]; then
    echo "ERROR: Critical vulnerabilities found in dependencies!"
    echo "Run 'npm audit fix' to resolve"
    exit 1
fi

echo "Dependency scan passed!"
exit 0