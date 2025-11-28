const scanner = require('sonarqube-scanner');

scanner(
  {
    serverUrl: process.env.SONAR_HOST_URL || 'http://localhost:9000',
    token: process.env.SONAR_TOKEN || '',
    options: {
      'sonar.projectKey': 'cicd-demo-app',
      'sonar.projectName': 'CI/CD Demo Application',
      'sonar.sources': 'src',
      'sonar.tests': 'tests',
      'sonar.javascript.lcov.reportPaths': 'coverage/lcov.info',
    },
  },
  () => process.exit()
);