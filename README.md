# CI/CD + AI Pipeline (cicd-ai-pipeline)

## Tools, Tech Stacks, and Platforms Used

- **Programming Languages:** Python, JavaScript (Node.js)
- **Frameworks & Libraries:** Express, Flask, scikit-learn, xgboost, prometheus_client, Jest
- **Containerization & Orchestration:** Docker, Minikube, Kubernetes, Helm, Kustomize
- **CI/CD & DevOps:** Jenkins, GitHub, GitHub Actions (optional)
- **Monitoring & Quality:** Prometheus, Grafana, SonarQube
- **Other Tools:** Sonar Scanner, Bash scripts (security scan, dependency scan, blue-green deployment), Python virtualenv
- **Platforms:** Linux, GitHub, Docker Hub (optional)


This repository demonstrates a complete, production-style CI/CD pipeline integrating modern DevOps, machine learning, and monitoring tools. It features:

- A Node.js application (Express server) for demo purposes, with automated testing and code quality checks.
- A Python-based ML pipeline for training and serving models (quality prediction, anomaly detection) using scikit-learn and xgboost.
- Containerization of all services using Docker, with orchestration via Kubernetes (Minikube for local development).
- Automated CI/CD using Jenkins (with Helm for deployment), plus optional GitHub Actions workflows.
- Comprehensive monitoring and code quality analysis using Prometheus (metrics), Grafana (dashboards), and SonarQube (static code analysis).
- Infrastructure-as-code for all deployments, with Kustomize overlays for dev/staging/prod environments.
- Security and dependency scanning via custom Bash scripts.

All components are designed to work together in a local or cloud-native Kubernetes cluster, with clear separation of concerns and extensibility for real-world use cases.

---


## Architecture Overview

**1. Application Layer**
  - `app/`: Node.js Express server with REST endpoints, unit tests (Jest), and SonarQube integration for code quality. Includes Dockerfile for containerization.

**2. Machine Learning Layer**
  - `ai-models/`: Python ML codebase.
    - `training/`: Scripts for training quality and anomaly detection models using scikit-learn and xgboost. Produces model artifacts (`quality_predictor.pkl`, `model_metrics.json`).
    - `serving/`: Flask server that loads trained models and exposes REST endpoints for predictions (`/predict/quality`, `/predict/anomaly`, `/predict/comprehensive`). Publishes Prometheus metrics for monitoring.
    - `models/`: Stores trained model files (excluded from git in production).
    - `requirements.txt`, `venv/`: Python dependencies and virtual environment for local development.

**3. Containerization & Orchestration**
  - Dockerfiles in both `app/` and `ai-models/` for building images.
  - Minikube used for local Kubernetes cluster.
  - `k8s/`: Kubernetes manifests for deploying all services, with Kustomize overlays for dev, staging, and production.

**4. CI/CD Pipeline**
  - Jenkins: Automated build, test, and deploy pipeline. Helm charts and manifests in `jenkins/` for easy setup.
  - GitHub Actions (optional): For automated CI workflows.
  - Bash scripts in `scripts/`: Security scan, dependency scan, blue-green deployment.

**5. Monitoring & Quality**
  - Prometheus: Collects metrics from the Flask model server and Node.js app.
  - Grafana: Visualizes metrics and dashboards.
  - SonarQube: Performs static code analysis on both Node.js and Python codebases. Integrated via Sonar Scanner and Jenkins pipeline.

**6. Infrastructure & Platform**
  - Linux: Development and deployment environment.
  - GitHub: Source code hosting and collaboration.
  - Docker Hub: Optional image registry for container images.

**7. Security & Compliance**
  - Custom Bash scripts for security and dependency scanning.
  - SonarQube for code quality and vulnerability detection.

This architecture ensures:
- Automated, reproducible builds and deployments
- Continuous integration and code quality enforcement
- Scalable, monitored ML model serving
- Easy local development and cloud migration

---

## Key components and responsibilities

- Demo app (`app/`): simple Express server used to illustrate CI/CD, code coverage, and Docker layering.
- AI training (`ai-models/training/`): training scripts produce `models/quality_predictor.pkl` and optional anomaly detector.
- Model server (`ai-models/serving/model_server.py`): Flask app exposing:
  - `GET /health` — basic health
  - `POST /predict/quality` — predict deployment quality
  - `POST /predict/anomaly` — anomaly detection
  - `POST /predict/comprehensive` — combined decision
  - `GET /metrics` — Prometheus metrics
- Kubernetes manifests (`k8s/`): base manifests and overlays for dev/staging/prod. Includes `ai-service`, `app`, `jenkins`, and monitoring components.

---

## Getting started (local, using Minikube)

Prereqs:
- Docker
- Minikube (tested with docker driver)
- kubectl
- Helm (for optional Jenkins install)

Recommended workflow (fast path):

1. Start Minikube

```bash
minikube start --driver=docker
```

2. Build images locally and load into Minikube (examples):

AI model server image

```bash
cd ai-models
docker build -t ai-model-server:latest .
minikube image load ai-model-server:latest
```

Node app image

```bash
cd app
docker build -t cicd-demo-app:1.0.0 .
minikube image load cicd-demo-app:1.0.0
```

3. Apply Kubernetes manifests

```bash
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/deployment.yaml     # app
kubectl apply -f k8s/ai-service/deployment.yaml   # ai-model-server
kubectl apply -f monitoring/sonarqube/sonarqube-deployment.yaml   # optional
```

4. Verify

```bash
kubectl get pods -n cicd-demo
kubectl get svc -n cicd-demo
minikube service --url demo-app-service -n cicd-demo
```

Notes:
- When using Minikube, image pulls from Docker Hub can be flaky; use `minikube image load` to ensure images are available inside the cluster.
- Some charts (like Jenkins) may pull many plugin images and time out. For local testing you can install Jenkins with reduced plugins or deploy a minimal Jenkins (or reuse the simpler k8s manifest in `k8s/jenkins/`).

---

## AI model training & serving

- Training: run from `ai-models/` (virtualenv recommended)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python training/train_quality_model.py
```

This produces `ai-models/models/quality_predictor.pkl` and `model_metrics.json`.

- Serving: Dockerfile in `ai-models/` builds the server image. The server expects models in `models/` within the image (or via a mounted volume). The Flask server exposes endpoints above and publishes Prometheus metrics.

Implementation notes and resilient behavior:
- `train_quality_model.py` now resolves dataset & model paths relative to the repository root so running from different cwd works.
- `serving/model_server.py` has a robust loading mechanism to import training modules directly by file path to avoid package import issues inside container images.
- Anomaly detector has a rule-based fallback if no trained anomaly model is present; this allows the server to run even when anomaly model artifact is missing.

---

## CI/CD notes and fixes included in this repo

- Docker build of `app/` originally failed because `package-lock.json` and `package.json` were out of sync. The repo contains a regenerated lockfile and an improved Dockerfile that copies `package.json` + `package-lock.json` and runs `npm ci --omit=dev` for reproducible installs.
- Jenkins Helm chart: the chart may try to pull many plugin images which can time out on Minikube. For local runs we used a simplified `values.yaml` (no plugins, reduced resources) or a direct k8s manifest to get a working Jenkins quickly.
- SonarQube and other images may need to be pulled locally and loaded into Minikube (`minikube image load`) if the cluster cannot reach Docker Hub reliably.

---

## Troubleshooting common issues

- `npm ci` fails in Docker build: regenerate `package-lock.json` locally with `npm install` to match `package.json`, or use the updated Dockerfile which expects `package-lock.json` present.
- `kubectl` openapi / validation errors: ensure Minikube is running (`minikube status`) and `kubectl config current-context` points to the Minikube cluster.
- ImagePullBackOff on Minikube: run `docker pull <image>` on the host and `minikube image load <image>`.
- Flask server import error `ModuleNotFoundError: No module named 'training.train_anomaly_model'`: image build may not have included `training/` or Python path differs. The server now loads training modules explicitly by file path so rebuild the image and redeploy.

---

## Recommended next steps / improvements

- Replace Flask development server with Gunicorn + Uvicorn (or similar) for production-grade serving; update Dockerfile accordingly.
- Add tests for the ML code (unit tests for feature preparation, small integration for training pipeline).
- Add automated image build + push steps to CI (e.g., GitHub Actions), then use Helm to deploy into a staging cluster.
- Store large model artifacts in an external artifact store (S3/MinIO) and mount or download at pod startup.

---

## Where to look in this repository

- `app/` — Node app, Dockerfile, CI test config
- `ai-models/training/` — training scripts
- `ai-models/serving/` — model server (Flask) and Docker entry
- `k8s/` — manifests to deploy app and ai-model-server
- `jenkins/`, `monitoring/` — pipeline tooling and monitoring

---

If you want, I can also:
- add a `README` in `ai-models/` with local dev steps and commands,
- add a small smoke-test that hits `/health` and `/predict/quality` after deployment,
- or create a simple GitHub Actions workflow that builds images and runs tests.

Happy to continue—what would you like next?
