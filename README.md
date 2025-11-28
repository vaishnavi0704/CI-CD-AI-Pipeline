# CI/CD + AI Pipeline (cicd-ai-pipeline)

This repository is a demo end-to-end CI/CD pipeline that includes a sample Node.js application, container images, a small ML subproject (training + model serving), Kubernetes manifests (kustomize/base overlays), and monitoring / quality tools (Prometheus/Grafana, SonarQube, Jenkins). The project is designed to be runnable locally with Docker and Minikube and easily adapted to CI systems.

---

## High-level architecture

- `app/` — Node.js demo application. Contains Dockerfile, frontend/server code, tests and sonar/sonar-scanner configuration.
- `ai-models/` — Python ML code and model serving.
  - `training/` — training scripts (quality & anomaly models) and small utilities.
  - `serving/` — Flask-based model server exposes REST endpoints and Prometheus metrics.
  - `models/` — trained model artifacts (gitignored in normal projects; included here for demo).
  - `requirements.txt` and a `venv/` for local development.
- `k8s/` — Kubernetes manifests (base + overlays) for deploying app, AI service, Jenkins and other infra.
- `monitoring/` — Grafana, Prometheus, SonarQube manifests and dashboards.
- `jenkins/` — Helm values and helper scripts for Jenkins.
- `scripts/` — utility scripts (security scan, dependency scan).

The pipeline demonstrates building images, running tests, scanning (SCA), and deploying to a Kubernetes cluster (Minikube for local testing). The AI models are trained locally and packaged into an image for running in-cluster.

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
