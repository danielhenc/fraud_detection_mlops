"""
Modelo base para detección de fraude.
Usa RandomForest con pipeline de preprocessing.
"""
import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import cross_val_score
import json

class FraudDetectionModel:
    def __init__(self):
        self.model = None
        self.pipeline = None
        self.model_metadata = {}
        
    def create_pipeline(self):
        """Crea el pipeline de preprocessing + modelo."""
        self.pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'  # Para manejar desbalance
            ))
        ])
        return self.pipeline
    
    def train(self, X_train, y_train):
        """Entrena el modelo."""
        print("Creando pipeline...")
        self.create_pipeline()
        
        print("Entrenando modelo...")
        self.pipeline.fit(X_train, y_train)
        
        # Cross-validation para evaluar
        cv_scores = cross_val_score(self.pipeline, X_train, y_train, cv=5, scoring='roc_auc')
        
        self.model_metadata = {
            'trained_at': datetime.now().isoformat(),
            'n_samples': len(X_train),
            'n_features': X_train.shape[1],
            'cv_auc_mean': float(cv_scores.mean()),
            'cv_auc_std': float(cv_scores.std()),
            'feature_names': list(X_train.columns)
        }
        
        print(f"Cross-validation AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
    def evaluate(self, X_test, y_test):
        """Evalúa el modelo en test set."""
        if self.pipeline is None:
            raise ValueError("Modelo no entrenado aún")
            
        y_pred = self.pipeline.predict(X_test)
        y_pred_proba = self.pipeline.predict_proba(X_test)[:, 1]
        
        test_auc = roc_auc_score(y_test, y_pred_proba)
        
        print("\n=== EVALUACIÓN EN TEST SET ===")
        print(f"Test AUC: {test_auc:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        # Actualizar metadata
        self.model_metadata.update({
            'test_auc': float(test_auc),
            'evaluated_at': datetime.now().isoformat()
        })
        
        return test_auc
    
    def predict(self, X):
        """Predice si una transacción es fraude."""
        if self.pipeline is None:
            raise ValueError("Modelo no entrenado aún")
        return self.pipeline.predict(X)
    
    def predict_proba(self, X):
        """Devuelve probabilidades de fraude."""
        if self.pipeline is None:
            raise ValueError("Modelo no entrenado aún")
        return self.pipeline.predict_proba(X)[:, 1]
    
    def save_model(self, model_dir='models'):
        """Guarda el modelo y metadatos."""
        os.makedirs(model_dir, exist_ok=True)
        
        # Guardar pipeline
        model_path = os.path.join(model_dir, 'fraud_model.joblib')
        joblib.dump(self.pipeline, model_path)
        
        # Guardar metadata
        metadata_path = os.path.join(model_dir, 'model_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(self.model_metadata, f, indent=2)
        
        print(f"Modelo guardado en: {model_path}")
        print(f"Metadata guardado en: {metadata_path}")
        
        return model_path
    
    def load_model(self, model_dir='models'):
        """Carga el modelo y metadatos."""
        model_path = os.path.join(model_dir, 'fraud_model.joblib')
        metadata_path = os.path.join(model_dir, 'model_metadata.json')
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo no encontrado en: {model_path}")
            
        self.pipeline = joblib.load(model_path)
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                self.model_metadata = json.load(f)
        
        print(f"Modelo cargado desde: {model_path}")
        return self

def train_initial_model():
    """Script para entrenar el modelo inicial."""
    print("=== ENTRENAMIENTO INICIAL DEL MODELO ===")
    
    # Cargar datos
    X_train = pd.read_csv('data/X_train.csv')
    X_test = pd.read_csv('data/X_test.csv')
    y_train = pd.read_csv('data/y_train.csv').iloc[:, 0]  # Tomar primera columna
    y_test = pd.read_csv('data/y_test.csv').iloc[:, 0]
    
    print(f"Train samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")
    
    # Crear y entrenar modelo
    model = FraudDetectionModel()
    model.train(X_train, y_train)
    
    # Evaluar
    test_auc = model.evaluate(X_test, y_test)
    
    # Guardar
    model.save_model()
    
    print(f"\n✅ Modelo entrenado exitosamente con AUC: {test_auc:.4f}")
    return model

if __name__ == "__main__":
    train_initial_model()