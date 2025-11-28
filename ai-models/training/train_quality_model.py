import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import xgboost as xgb
import joblib
import json
import os
from pathlib import Path

class QualityPredictor:
    def __init__(self):
        self.model = None
        self.feature_columns = None
        
    def prepare_features(self, df):
        """Prepare features for training"""
        # Feature engineering
        df = df.copy()
        
        # Derived features
        df['quality_score'] = (
            0.3 * df['test_pass_rate'] +
            0.25 * df['code_coverage'] +
            0.25 * (1 - np.minimum(df['security_vulnerabilities'] / 10, 1)) +
            0.2 * (1 - df['code_complexity'] / 10)
        )
        
        df['risk_score'] = (
            df['security_vulnerabilities'] * 0.4 +
            (1 - df['test_pass_rate']) * 30 +
            (1 - df['code_coverage']) * 20 +
            df['code_complexity'] * 0.1
        )
        
        # Select features
        self.feature_columns = [
            'test_pass_rate',
            'code_coverage',
            'security_vulnerabilities',
            'code_complexity',
            'lines_of_code',
            'deployment_frequency',
            'quality_score',
            'risk_score'
        ]
        
        X = df[self.feature_columns]
        # Return target column if present, otherwise None (useful for predict-time features)
        y = df['deployment_success'] if 'deployment_success' in df.columns else None
        return X, y
    
    def train(self, df):
        """Train the quality prediction model"""
        print("Preparing features...")
        X, y = self.prepare_features(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training samples: {len(X_train)}")
        print(f"Test samples: {len(X_test)}")
        
        # Train XGBoost model
        print("\nTraining XGBoost model...")
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        print("\nEvaluating model...")
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        auc_score = roc_auc_score(y_test, y_pred_proba)
        print(f"\nROC AUC Score: {auc_score:.4f}")
        
        # Feature importance
        print("\nFeature Importance:")
        for feature, importance in zip(self.feature_columns, self.model.feature_importances_):
            print(f"{feature}: {importance:.4f}")
        
        return {
            'accuracy': self.model.score(X_test, y_test),
            'auc': auc_score,
            'feature_importance': dict(zip(self.feature_columns, 
                                          self.model.feature_importances_.tolist()))
        }
    
    def predict(self, features):
        """Predict deployment quality"""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Ensure features are in correct format
        if isinstance(features, dict):
            features_df = pd.DataFrame([features])
            X, _ = self.prepare_features(features_df)
        else:
            X = features[self.feature_columns]
        
        prediction = self.model.predict(X)[0]
        probability = self.model.predict_proba(X)[0]
        
        return {
            'success_prediction': int(prediction),
            'success_probability': float(probability[1]),
            'recommendation': self._get_recommendation(float(probability[1]))
        }
    
    def _get_recommendation(self, prob):
        """Get deployment recommendation based on probability"""
        if prob >= 0.85:
            return "AUTO_DEPLOY"
        elif prob >= 0.70:
            return "MANUAL_APPROVAL"
        else:
            return "BLOCK_DEPLOYMENT"
    
    def save_model(self, path='models/quality_predictor.pkl'):
        """Save trained model"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'feature_columns': self.feature_columns
        }, path)
        print(f"Model saved to {path}")
    
    def load_model(self, path='models/quality_predictor.pkl'):
        """Load trained model"""
        data = joblib.load(path)
        self.model = data['model']
        self.feature_columns = data['feature_columns']
        print(f"Model loaded from {path}")

if __name__ == '__main__':
    # Resolve repository-relative paths (robust to current working directory)
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / 'data' / 'deployments.json'
    models_dir = base_dir / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}\nPlease ensure deployments.json exists under: {base_dir / 'data'}")
    df = pd.read_json(data_path)
    
    # Train model
    predictor = QualityPredictor()
    metrics = predictor.train(df)
    
    # Save model (to repo-relative models/ directory)
    predictor.save_model(str(models_dir / 'quality_predictor.pkl'))

    # Save metrics
    with open(models_dir / 'model_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print("\nModel training complete!")
    
    # Test prediction
    sample_deployment = {
        'test_pass_rate': 0.95,
        'code_coverage': 0.85,
        'security_vulnerabilities': 1,
        'code_complexity': 3.5,
        'lines_of_code': 2500,
        'deployment_frequency': 15.0
    }
    
    result = predictor.predict(sample_deployment)
    print("\nSample Prediction:")
    print(json.dumps(result, indent=2))