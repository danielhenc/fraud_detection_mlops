"""
Sistema de reentrenamiento automático.
Simula nuevos datos, reentrena el modelo, valida métricas y actualiza.
"""
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import logging
from typing import Tuple, Dict
import shutil

from model import FraudDetectionModel
from data_loader import load_and_process_data

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetrainingSystem:
    def __init__(self, min_auc_threshold=0.7, max_model_age_days=7):
        self.min_auc_threshold = min_auc_threshold
        self.max_model_age_days = max_model_age_days
        self.retraining_log = []
    
    def should_retrain(self) -> Tuple[bool, str]:
        """Determina si el modelo necesita reentrenamiento."""
        reasons = []
        
        # Verificar si existe modelo actual
        model_path = 'models/fraud_model.joblib'
        metadata_path = 'models/model_metadata.json'
        
        if not os.path.exists(model_path):
            return True, "No existe modelo entrenado"
        
        # Cargar metadata del modelo actual
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except:
            return True, "No se pudo leer metadata del modelo"
        
        # Verificar edad del modelo
        if 'trained_at' in metadata:
            trained_at = datetime.fromisoformat(metadata['trained_at'])
            model_age = (datetime.now() - trained_at).days
            
            if model_age > self.max_model_age_days:
                reasons.append(f"Modelo muy antiguo ({model_age} días)")
        
        # Verificar performance (si existe test_auc)
        if 'test_auc' in metadata:
            if metadata['test_auc'] < self.min_auc_threshold:
                reasons.append(f"AUC bajo ({metadata['test_auc']:.4f} < {self.min_auc_threshold})")
        
        # Por ahora, siempre reentrenar para demostrar el flujo
        reasons.append("Reentrenamiento programado")
        
        return len(reasons) > 0, "; ".join(reasons)
    
    def simulate_new_data(self, n_samples=2000) -> pd.DataFrame:
        """Simula llegada de nuevos datos de transacciones."""
        logger.info(f"Simulando {n_samples} nuevas transacciones...")
        
        # Para simplificar, generamos datos sintéticos basados en distribuciones conocidas
        np.random.seed(int(datetime.now().timestamp()) % 1000)
        
        # Generar features basándose en patrones del dataset original
        data = {
            'Time': np.random.uniform(0, 172800, n_samples),  # 48 horas en segundos
            'V1': np.random.normal(-0.5, 2.0, n_samples),
            'V2': np.random.normal(0.0, 1.5, n_samples),
            'V4': np.random.normal(0.0, 1.8, n_samples),
            'V11': np.random.normal(0.0, 2.2, n_samples),
            'Amount': np.random.lognormal(3.0, 2.0, n_samples)
        }
        
        # Generar etiquetas con aproximadamente 0.17% de fraude (similar al dataset real)
        fraud_rate = 0.0017
        n_fraud = int(n_samples * fraud_rate)
        labels = [1] * n_fraud + [0] * (n_samples - n_fraud)
        np.random.shuffle(labels)
        
        # Para casos de fraude, modificar algunas features para hacerlos más detectables
        df = pd.DataFrame(data)
        df['Class'] = labels
        
        # Modificar patrones en casos de fraude
        fraud_mask = df['Class'] == 1
        df.loc[fraud_mask, 'V1'] = np.random.normal(-3.0, 1.0, fraud_mask.sum())
        df.loc[fraud_mask, 'Amount'] = np.random.lognormal(4.5, 1.5, fraud_mask.sum())
        
        logger.info(f"Datos simulados: {len(df)} transacciones, {fraud_mask.sum()} fraudes ({fraud_mask.mean():.4f})")
        
        return df
    
    def validate_model_performance(self, model: FraudDetectionModel, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """Valida el performance del modelo reentrenado."""
        logger.info("Validando performance del modelo...")
        
        test_auc = model.evaluate(X_test, y_test)
        
        validation_results = {
            'test_auc': test_auc,
            'meets_threshold': test_auc >= self.min_auc_threshold,
            'validation_timestamp': datetime.now().isoformat()
        }
        
        return validation_results
    
    def backup_current_model(self):
        """Hace backup del modelo actual antes de reemplazarlo."""
        if os.path.exists('models/fraud_model.joblib'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f'models/backup_{timestamp}'
            os.makedirs(backup_dir, exist_ok=True)
            
            shutil.copy('models/fraud_model.joblib', f'{backup_dir}/fraud_model.joblib')
            if os.path.exists('models/model_metadata.json'):
                shutil.copy('models/model_metadata.json', f'{backup_dir}/model_metadata.json')
            
            logger.info(f"Backup creado en: {backup_dir}")
            return backup_dir
        return None
    
    def retrain_model(self) -> Dict:
        """Ejecuta el proceso completo de reentrenamiento."""
        logger.info("=== INICIANDO REENTRENAMIENTO ===")
        
        retrain_log = {
            'started_at': datetime.now().isoformat(),
            'status': 'started'
        }
        
        try:
            # 1. Verificar si necesita reentrenamiento
            should_retrain, reason = self.should_retrain()
            retrain_log['should_retrain'] = should_retrain
            retrain_log['reason'] = reason
            
            if not should_retrain:
                logger.info(f"No se requiere reentrenamiento: {reason}")
                retrain_log['status'] = 'skipped'
                return retrain_log
            
            logger.info(f"Iniciando reentrenamiento: {reason}")
            
            # 2. Backup del modelo actual
            backup_path = self.backup_current_model()
            retrain_log['backup_path'] = backup_path
            
            # 3. Simular nuevos datos
            new_data = self.simulate_new_data()
            retrain_log['new_data_samples'] = len(new_data)
            retrain_log['new_data_fraud_rate'] = (new_data['Class'] == 1).mean()
            
            # 4. Combinar con datos existentes (si existen)
            if os.path.exists('data/fraud_data_processed.csv'):
                existing_data = pd.read_csv('data/fraud_data_processed.csv')
                combined_data = pd.concat([existing_data, new_data], ignore_index=True)
                logger.info(f"Combinando con datos existentes: {len(existing_data)} + {len(new_data)} = {len(combined_data)}")
            else:
                combined_data = new_data
                logger.info("Usando solo datos nuevos para entrenamiento")
            
            # 5. Dividir datos
            from sklearn.model_selection import train_test_split
            X = combined_data.drop('Class', axis=1)
            y = combined_data['Class']
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            retrain_log['train_samples'] = len(X_train)
            retrain_log['test_samples'] = len(X_test)
            
            # 6. Entrenar nuevo modelo
            logger.info("Entrenando nuevo modelo...")
            model = FraudDetectionModel()
            model.train(X_train, y_train)
            
            # 7. Validar performance
            validation_results = self.validate_model_performance(model, X_test, y_test)
            retrain_log['validation'] = validation_results
            
            # 8. Decidir si desplegar el nuevo modelo
            if validation_results['meets_threshold']:
                logger.info(f"Nuevo modelo cumple threshold (AUC: {validation_results['test_auc']:.4f})")
                
                # Guardar nuevo modelo
                model.save_model()
                
                # Actualizar datos de entrenamiento
                combined_data.to_csv('data/fraud_data_processed.csv', index=False)
                
                retrain_log['status'] = 'success'
                retrain_log['deployed'] = True
                
                logger.info("Reentrenamiento completado exitosamente")
                
            else:
                logger.warning(f"Nuevo modelo no cumple threshold (AUC: {validation_results['test_auc']:.4f})")
                retrain_log['status'] = 'failed_validation'
                retrain_log['deployed'] = False
                
                # Restaurar modelo anterior si existe backup
                if backup_path:
                    logger.info("Restaurando modelo anterior...")
                    shutil.copy(f'{backup_path}/fraud_model.joblib', 'models/fraud_model.joblib')
                    if os.path.exists(f'{backup_path}/model_metadata.json'):
                        shutil.copy(f'{backup_path}/model_metadata.json', 'models/model_metadata.json')
            
        except Exception as e:
            logger.error(f"Error durante reentrenamiento: {e}")
            retrain_log['status'] = 'error'
            retrain_log['error'] = str(e)
        
        finally:
            retrain_log['completed_at'] = datetime.now().isoformat()
            
            # Guardar log del reentrenamiento
            self.retraining_log.append(retrain_log)
            self.save_retraining_log()
        
        return retrain_log
    
    def save_retraining_log(self):
        """Guarda el historial de reentrenamientos."""
        log_path = 'models/retraining_log.json'
        with open(log_path, 'w') as f:
            json.dump(self.retraining_log, f, indent=2)
    
    def get_retraining_history(self) -> list:
        """Obtiene el historial de reentrenamientos."""
        log_path = 'models/retraining_log.json'
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                return json.load(f)
        return []

def run_retraining():
    """Script principal para ejecutar reentrenamiento."""
    system = RetrainingSystem()
    result = system.retrain_model()
    
    print(f"\n=== RESULTADO DEL REENTRENAMIENTO ===")
    print(f"Status: {result['status']}")
    if 'reason' in result:
        print(f"Razón: {result['reason']}")
    if 'validation' in result:
        print(f"AUC del nuevo modelo: {result['validation']['test_auc']:.4f}")
    if 'deployed' in result:
        print(f"Modelo desplegado: {'Sí' if result['deployed'] else 'No'}")
    
    return result

if __name__ == "__main__":
    run_retraining()