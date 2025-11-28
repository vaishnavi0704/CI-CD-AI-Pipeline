pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'cicd-demo-app'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        DOCKER_REGISTRY = 'localhost:5000'
        KUBE_NAMESPACE = 'cicd-demo'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                dir('app') {
                    sh 'npm ci'
                }
            }
        }
        
        stage('Unit Tests') {
            steps {
                dir('app') {
                    sh 'npm test'
                }
            }
            post {
                always {
                    junit 'app/coverage/junit.xml'
                    publishHTML([
                        reportDir: 'app/coverage',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('Code Quality Analysis') {
            steps {
                echo 'Running code quality checks...'
                // Will add SonarQube integration later
            }
        }
        
        stage('Security Scan') {
            steps {
                echo 'Running security scans...'
                // Will add Trivy scan later
            }
        }
        
        stage('Build Docker Image') {
            steps {
                dir('app') {
                    script {
                        docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                        docker.build("${DOCKER_IMAGE}:latest")
                    }
                }
            }
        }
        
        stage('AI Quality Gate') {
            steps {
                echo 'Running AI quality prediction...'
                // Will implement AI model later
                script {
                    def qualityScore = 0.85 // Placeholder
                    if (qualityScore < 0.70) {
                        error("Quality score ${qualityScore} is below threshold")
                    }
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    sh """
                        kubectl set image deployment/demo-app \
                          demo-app=${DOCKER_IMAGE}:${DOCKER_TAG} \
                          -n ${KUBE_NAMESPACE}
                        
                        kubectl rollout status deployment/demo-app \
                          -n ${KUBE_NAMESPACE}
                    """
                }
            }
        }
        
        stage('Health Check') {
            steps {
                script {
                    sleep(time: 30, unit: 'SECONDS')
                    sh """
                        kubectl run curl-test --image=curlimages/curl --rm -i --restart=Never \
                          -n ${KUBE_NAMESPACE} \
                          -- curl http://demo-app-service/health
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
            // Add rollback logic here
        }
        always {
            cleanWs()
        }
    }
}