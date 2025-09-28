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

from model import FraudDetectionModel

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title="Fraud Detection API",
    description="API para detección de fraude en transacciones bancarias",
    version="1.0.0"
)

# Cargar modelo al iniciar la aplicación
model = None

@app.on_event("startup")
async def startup_event():
    """Cargar modelo al iniciar la API."""
    global model
    try:
        model = FraudDetectionModel()
        model.load_model()
        logger.info("Modelo cargado exitosamente")
    except Exception as e:
        logger.error(f"Error cargando modelo: {e}")
        # En producción, podrías querer fallar aquí
        model = None

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
    
    return {
        "status": "healthy",
        "model_status": model_status,
        "model_metadata": model.model_metadata if model else {},
        "timestamp": datetime.now().isoformat()
    }

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
    uvicorn.run(app, host="0.0.0.0", port=8000)