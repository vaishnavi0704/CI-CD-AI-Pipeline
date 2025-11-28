import json
import os
from datetime import datetime
import pandas as pd

class DeploymentDataCollector:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.deployments_file = os.path.join(data_dir, 'deployments.json')
        
    def collect_deployment_data(self, deployment_data):
        """
        Collect deployment metrics
        
        deployment_data should include:
        - build_number
        - test_pass_rate
        - code_coverage
        - security_vulnerabilities
        - code_complexity
        - deployment_success
        - error_rate
        - response_time
        """
        deployment_data['timestamp'] = datetime.now().isoformat()
        
        # Load existing data
        if os.path.exists(self.deployments_file):
            with open(self.deployments_file, 'r') as f:
                deployments = json.load(f)
        else:
            deployments = []
        
        # Append new deployment
        deployments.append(deployment_data)
        
        # Save updated data
        with open(self.deployments_file, 'w') as f:
            json.dump(deployments, f, indent=2)
        
        print(f"Deployment data collected: Build #{deployment_data['build_number']}")
        
    def get_deployments_df(self):
        """Load deployments as pandas DataFrame"""
        if os.path.exists(self.deployments_file):
            with open(self.deployments_file, 'r') as f:
                deployments = json.load(f)
            return pd.DataFrame(deployments)
        return pd.DataFrame()
    
    def generate_sample_data(self, n_samples=100):
        """Generate sample deployment data for training"""
        import numpy as np
        
        np.random.seed(42)
        
        for i in range(n_samples):
            # Simulate deployment metrics
            test_pass_rate = np.random.uniform(0.7, 1.0)
            code_coverage = np.random.uniform(0.5, 0.95)
            security_vulns = np.random.poisson(2)
            code_complexity = np.random.uniform(1, 10)
            
            # Success probability based on metrics
            success_prob = (
                0.3 * test_pass_rate +
                0.25 * code_coverage +
                0.25 * (1 - min(security_vulns / 10, 1)) +
                0.2 * (1 - code_complexity / 10)
            )
            
            deployment_success = 1 if np.random.random() < success_prob else 0
            
            # Post-deployment metrics
            error_rate = np.random.uniform(0, 0.1) if deployment_success else np.random.uniform(0.05, 0.3)
            response_time = np.random.uniform(100, 500) if deployment_success else np.random.uniform(400, 2000)
            
            deployment_data = {
                'build_number': i + 1,
                'test_pass_rate': round(test_pass_rate, 3),
                'code_coverage': round(code_coverage, 3),
                'security_vulnerabilities': security_vulns,
                'code_complexity': round(code_complexity, 2),
                'lines_of_code': int(np.random.uniform(500, 5000)),
                'deployment_frequency': round(np.random.uniform(1, 30), 1),
                'deployment_success': deployment_success,
                'error_rate': round(error_rate, 4),
                'response_time_ms': round(response_time, 2)
            }
            
            self.collect_deployment_data(deployment_data)
        
        print(f"Generated {n_samples} sample deployments")

if __name__ == '__main__':
    collector = DeploymentDataCollector()
    collector.generate_sample_data(100)
    
    df = collector.get_deployments_df()
    print("\nSample data:")
    print(df.head())
    print(f"\nTotal deployments: {len(df)}")
    print(f"Success rate: {df['deployment_success'].mean():.2%}")