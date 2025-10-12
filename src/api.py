"""
API FastAPI para detección de fraude.
Endpoints para predicción y health check.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import List, Dict, Any
import logging
import logging.config
import threading
import time
import json

from model import FraudDetectionModel
from config import config

# Configurar logging usando la configuración centralizada
logging.config.dictConfig(config.log_config)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION
)

# Variables globales para el modelo y control de recarga
model = None
model_lock = threading.Lock()
model_last_modified = None
model_watcher_running = False

def load_model():
    """Función para cargar/recargar el modelo de forma thread-safe."""
    global model, model_last_modified
    
    with model_lock:
        try:
            new_model = FraudDetectionModel()
            new_model.load_model()
            
            # Actualizar modelo y timestamp
            model = new_model
            model_path = "models/fraud_model.joblib"
            if os.path.exists(model_path):
                model_last_modified = os.path.getmtime(model_path)
            
            logger.info(f"Modelo cargado/recargado exitosamente. Versión: {model.model_metadata.get('version', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            return False

def model_file_watcher():
    """Watcher para detectar cambios en el archivo del modelo."""
    global model_watcher_running, model_last_modified
    
    model_path = config.MODEL_PATH
    metadata_path = config.METADATA_PATH
    
    while model_watcher_running:
        try:
            # Verificar si alguno de los archivos del modelo cambió
            current_model_time = os.path.getmtime(model_path) if os.path.exists(model_path) else None
            current_metadata_time = os.path.getmtime(metadata_path) if os.path.exists(metadata_path) else None
            
            # Si el archivo del modelo cambió
            if current_model_time and (model_last_modified is None or current_model_time > model_last_modified):
                logger.info("Detectado cambio en el archivo del modelo. Recargando...")
                if load_model():
                    logger.info("Modelo recargado automáticamente")
                else:
                    logger.error("Falló la recarga automática del modelo")
            
            time.sleep(config.WATCHER_INTERVAL)  # Verificar según configuración
            
        except Exception as e:
            logger.error(f"Error en model watcher: {e}")
            time.sleep(60)  # Esperar más si hay error

@app.on_event("startup")
async def startup_event():
    """Cargar modelo e iniciar watcher al iniciar la API."""
    global model_watcher_running
    
    # Cargar modelo inicial
    if not load_model():
        logger.warning("No se pudo cargar el modelo inicial")
    
    # Iniciar watcher en background solo si está habilitado
    if config.ENABLE_MODEL_WATCHER:
        model_watcher_running = True
        watcher_thread = threading.Thread(target=model_file_watcher, daemon=True)
        watcher_thread.start()
        logger.info("Model file watcher iniciado")
    else:
        logger.info("Model file watcher deshabilitado por configuración")

@app.on_event("shutdown")
async def shutdown_event():
    """Detener watcher al cerrar la API."""
    global model_watcher_running
    model_watcher_running = False
    logger.info("API shutting down...")

# Modelos Pydantic para requests/responses
class TransactionRequest(BaseModel):
    """Modelo para request de predicción."""
    Time: float
    V1: float
    V2: float
    V4: float
    V11: float
    Amount: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "Time": 0.0,
                "V1": -1.359807,
                "V2": -0.072781,
                "V4": 2.536347,
                "V11": 1.175480,
                "Amount": 149.62
            }
        }

class TransactionResponse(BaseModel):
    """Modelo para response de predicción."""
    is_fraud: bool
    fraud_probability: float
    risk_score: str
    prediction_timestamp: str

class BatchTransactionRequest(BaseModel):
    """Modelo para batch de transacciones."""
    transactions: List[TransactionRequest]

class BatchTransactionResponse(BaseModel):
    """Response para batch de predicciones."""
    predictions: List[TransactionResponse]
    batch_summary: Dict[str, Any]

# Endpoints
@app.get("/")
async def root():
    """Health check básico."""
    return {
        "message": "Fraud Detection API", 
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check detallado.""" 
    model_status = "loaded" if model is not None else "not_loaded"
    model_path = "models/fraud_model.joblib"
    
    return {
        "status": "healthy",
        "model_status": model_status,
        "model_metadata": model.model_metadata if model else {},
        "model_last_modified": datetime.fromtimestamp(model_last_modified).isoformat() if model_last_modified else None,
        "model_file_exists": os.path.exists(model_path),
        "watcher_running": model_watcher_running,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/reload-model")
async def reload_model():
    """Endpoint para recargar manualmente el modelo."""
    logger.info("Recarga manual del modelo solicitada")
    
    if load_model():
        return {
            "status": "success",
            "message": "Modelo recargado exitosamente",
            "model_metadata": model.model_metadata if model else {},
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail="Error recargando el modelo. Ver logs para más detalles."
        )

@app.post("/predict", response_model=TransactionResponse)
async def predict_fraud(transaction: TransactionRequest):
    """Predice si una transacción es fraude."""
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible")
    
    try:
        # Convertir a DataFrame
        df = pd.DataFrame([transaction.dict()])
        
        # Predecir
        prediction = model.predict(df)[0]
        probability = model.predict_proba(df)[0]
        
        # Determinar nivel de riesgo
        if probability >= 0.8:
            risk_score = "HIGH"
        elif probability >= 0.5:
            risk_score = "MEDIUM"
        elif probability >= 0.2:
            risk_score = "LOW"
        else:
            risk_score = "VERY_LOW"
        
        logger.info(f"Predicción: {prediction}, Probabilidad: {probability:.4f}")
        
        return TransactionResponse(
            is_fraud=bool(prediction),
            fraud_probability=float(probability),
            risk_score=risk_score,
            prediction_timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")

@app.post("/predict/batch", response_model=BatchTransactionResponse)
async def predict_fraud_batch(batch: BatchTransactionRequest):
    """Predice fraude para un lote de transacciones."""
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible")
    
    try:
        # Convertir batch a DataFrame
        transactions_data = [t.dict() for t in batch.transactions]
        df = pd.DataFrame(transactions_data)
        
        # Predecir todo el batch
        predictions = model.predict(df)
        probabilities = model.predict_proba(df)
        
        # Crear responses individuales
        responses = []
        fraud_count = 0
        
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            if prob >= 0.8:
                risk_score = "HIGH"
            elif prob >= 0.5:
                risk_score = "MEDIUM"
            elif prob >= 0.2:
                risk_score = "LOW"
            else:
                risk_score = "VERY_LOW"
            
            if pred:
                fraud_count += 1
            
            responses.append(TransactionResponse(
                is_fraud=bool(pred),
                fraud_probability=float(prob),
                risk_score=risk_score,
                prediction_timestamp=datetime.now().isoformat()
            ))
        
        # Estadísticas del batch
        batch_summary = {
            "total_transactions": len(batch.transactions),
            "fraud_detected": fraud_count,
            "fraud_rate": fraud_count / len(batch.transactions),
            "avg_fraud_probability": float(probabilities.mean()),
            "max_fraud_probability": float(probabilities.max())
        }
        
        logger.info(f"Batch procesado: {len(batch.transactions)} transacciones, {fraud_count} fraudes detectados")
        
        return BatchTransactionResponse(
            predictions=responses,
            batch_summary=batch_summary
        )
        
    except Exception as e:
        logger.error(f"Error en batch prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Error en batch prediction: {str(e)}")

@app.get("/model/info")
async def model_info():
    """Información del modelo actual."""
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible")
    
    return {
        "model_metadata": model.model_metadata,
        "status": "loaded",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Iniciando API en {config.API_HOST}:{config.API_PORT}")
    logger.info(f"Entorno: {config.ENV}")
    logger.info(f"Model watcher: {'habilitado' if config.ENABLE_MODEL_WATCHER else 'deshabilitado'}")
    
    uvicorn.run(
        app, 
        host=config.API_HOST, 
        port=config.API_PORT,
        log_level=config.LOG_LEVEL.lower(),
        access_log=not config.is_production()  # Desactivar access logs en producción
    )