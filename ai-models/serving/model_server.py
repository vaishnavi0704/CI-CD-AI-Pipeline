from flask import Flask, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import importlib.util
# Load training modules by file path to avoid package/import ambiguity inside containers
base_dir = os.path.dirname(os.path.dirname(__file__))

def load_module_from_training(filename, module_name=None):
    path = os.path.join(base_dir, 'training', filename)
    name = module_name or os.path.splitext(filename)[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Quality predictor module
_qmod = load_module_from_training('train_quality_model.py', 'train_quality_model')
QualityPredictor = _qmod.QualityPredictor

# Anomaly detector module
_amod = load_module_from_training('train_anomaly_model.py', 'train_anomaly_model')
AnomalyDetector = _amod.AnomalyDetector
from prometheus_client import Counter, Histogram, generate_latest
import time

app = Flask(__name__)

# Load models
quality_predictor = QualityPredictor()
quality_predictor.load_model('../models/quality_predictor.pkl')

anomaly_detector = AnomalyDetector()
anomaly_detector.load_model('../models/anomaly_detector.pkl')

# Prometheus metrics
prediction_counter = Counter('predictions_total', 'Total predictions made')
prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/predict/quality', methods=['POST'])
def predict_quality():
    start_time = time.time()
    
    try:
        data = request.get_json()
        result = quality_predictor.predict(data)
        
        prediction_counter.inc()
        prediction_latency.observe(time.time() - start_time)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/predict/anomaly', methods=['POST'])
def predict_anomaly():
    start_time = time.time()
    
    try:
        data = request.get_json()
        result = anomaly_detector.detect(data)
        
        prediction_counter.inc()
        prediction_latency.observe(time.time() - start_time)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/predict/comprehensive', methods=['POST'])
def predict_comprehensive():
    """Comprehensive prediction combining quality and anomaly detection"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        # Quality prediction
        quality_result = quality_predictor.predict(data)
        
        # Anomaly detection
        anomaly_result = anomaly_detector.detect(data)
        
        # Combined decision
        final_recommendation = quality_result['recommendation']
        
        # Override if anomaly detected
        if anomaly_result['is_anomaly'] and anomaly_result['severity'] in ['MEDIUM', 'HIGH']:
            final_recommendation = 'MANUAL_APPROVAL'
        
        if anomaly_result['is_anomaly'] and anomaly_result['severity'] == 'HIGH':
            final_recommendation = 'BLOCK_DEPLOYMENT'
        
        result = {
            'quality_prediction': quality_result,
            'anomaly_detection': anomaly_result,
            'final_recommendation': final_recommendation,
            'confidence': quality_result['success_probability']
        }
        
        prediction_counter.inc()
        prediction_latency.observe(time.time() - start_time)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/metrics', methods=['GET'])
def metrics():
    return generate_latest(), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)