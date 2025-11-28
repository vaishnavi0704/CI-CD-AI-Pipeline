import joblib
import os
import numpy as np
import pandas as pd

class AnomalyDetector:
    """Simple anomaly detector wrapper.

    Behavior:
    - If a pre-trained model is present (joblib), it will be used.
    - Otherwise a lightweight rule-based detector is used so the server can run.
    """
    def __init__(self):
        self.model = None

    def load_model(self, path='models/anomaly_detector.pkl'):
        """Load a joblib model if it exists, otherwise keep None."""
        if os.path.isabs(path):
            model_path = path
        else:
            # model path relative to repo root (ai-models/models/...)
            base_dir = os.path.dirname(os.path.dirname(__file__))
            model_path = os.path.join(base_dir, path)

        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            print(f"Anomaly detector loaded from {model_path}")
        else:
            self.model = None
            print(f"No anomaly model found at {model_path}; using rule-based fallback")

    def detect(self, features):
        """Detect anomalies in a single feature dict or DataFrame row.

        Returns a dict: {is_anomaly: bool, severity: 'LOW'|'MEDIUM'|'HIGH', score: float}
        """
        # Normalize input
        if isinstance(features, dict):
            df = pd.DataFrame([features])
        elif isinstance(features, pd.DataFrame):
            df = features.copy()
        else:
            # try to coerce
            df = pd.DataFrame(features)

        # If a trained model exists, use it
        if self.model is not None:
            try:
                probs = self.model.predict_proba(df)[:, 1]
                score = float(probs[0])
                is_anomaly = score > 0.5
                severity = 'LOW'
                if score > 0.8:
                    severity = 'HIGH'
                elif score > 0.6:
                    severity = 'MEDIUM'
                return {'is_anomaly': bool(is_anomaly), 'severity': severity, 'score': score}
            except Exception:
                # fallback to rule-based if model fails
                pass

        # Rule-based fallback:
        score = 0.0
        # Use available fields conservatively
        if 'security_vulnerabilities' in df.columns:
            score += min(df.iloc[0]['security_vulnerabilities'] / 10.0, 1.0) * 0.6
        if 'risk_score' in df.columns:
            rs = df.iloc[0]['risk_score']
            # normalize risk_score roughly into 0..1 (assumes risk_score reasonable scale)
            score += min(rs / 100.0, 1.0) * 0.3
        if 'test_pass_rate' in df.columns:
            score += (1 - df.iloc[0]['test_pass_rate']) * 0.1

        score = float(np.clip(score, 0.0, 1.0))
        is_anomaly = score > 0.4
        if score > 0.75:
            severity = 'HIGH'
        elif score > 0.5:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'

        return {'is_anomaly': bool(is_anomaly), 'severity': severity, 'score': score}
