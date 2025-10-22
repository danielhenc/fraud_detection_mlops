# MLOps End-to-End: Detección de Fraude Bancario

## Descripción

Proyecto MLOps completo para detección de fraude bancario implementando:
- **API REST** con FastAPI para predicciones en tiempo real
- **Reentrenamiento automático** con GitHub Actions 
- **Containerización** con Docker
- **Monitoreo de datos** y validación de modelos
- **Testing comprehensivo** para garantizar calidad

## Arquitectura

```
├── src/
│   ├── api.py              # FastAPI REST API
│   ├── model.py            # Modelo RandomForest + pipeline
│   ├── data_loader.py      # Carga y procesamiento de datos
│   ├── data_monitor.py     # Monitoreo para reentrenamiento
│   ├── retrain.py          # Sistema de reentrenamiento
│   └── scheduler.py        # Scheduler para cron jobs
├── data/
│   ├── X_train.csv         # Features de entrenamiento
│   ├── y_train.csv         # Labels de entrenamiento
│   └── fraud_data_processed.csv  # Dataset procesado
├── models/
│   ├── fraud_model.joblib  # Modelo serializado
│   └── model_metadata.json # Metadatos del modelo
├── .github/workflows/
│   └── auto-retrain.yml    # Pipeline CI/CD automático
├── Dockerfile              # Containerización
└── test_api.py             # Suite de tests
```

## Quick Start

### 1. Instalación

```bash
git clone <tu-repo>
cd fraud_detection_mlops
pip install -r requirements.txt
```

### 2. Entrenar modelo inicial

```bash
python src/model.py
# Modelo entrenado con AUC: 0.9998
```

### 3. Ejecutar API

```bash
python src/api.py
# API corriendo en http://localhost:8000
```

### 4. Probar predicciones

```bash
# Test simple
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"Time": 0, "V1": -1.36, "V2": -0.07, "V4": 2.54, "V11": 1.18, "Amount": 149.62}'

# Respuesta: {"prediction": 0, "probability": 0.0012, "is_fraud": false}
```

## Endpoints de la API

| Endpoint | Método | Descripción |
|----------|---------|-------------|
| `/health` | GET | Status de la API y modelo |
| `/model/info` | GET | Información y métricas del modelo |
| `/predict` | POST | Predicción individual |
| `/predict/batch` | POST | Predicciones en lote |

### Ejemplos de uso:

**Health Check:**
```bash
curl http://localhost:8000/health
# {"status": "healthy", "model_loaded": true, "timestamp": "..."}
```

**Información del modelo:**
```bash
curl http://localhost:8000/model/info
# {"model_type": "RandomForestClassifier", "features": [...], "metrics": {...}}
```

**Predicción batch:**
```json
POST /predict/batch
{
  "transactions": [
    {"Time": 0, "V1": -1.36, "V2": -0.07, "V4": 2.54, "V11": 1.18, "Amount": 149.62},
    {"Time": 1, "V1": 1.19, "V2": 0.27, "V4": 0.13, "V11": -0.75, "Amount": 2.69}
  ]
}
```

## Reentrenamiento Automático

### ¿Cómo funciona?

1. **Trigger:** Se activa cuando modificas archivos en `data/`
2. **Monitoreo:** Detecta si hay >100 filas nuevas (configurable)  
3. **Reentrenamiento:** Entrena nuevo modelo si es necesario
4. **Validación:** AUC mínimo 0.85, degradación máxima 5%
5. **Backup:** Respaldo automático del modelo anterior
6. **Deploy:** Actualiza el modelo si pasa validaciones

### Configuración:

```bash
# Verificar estado actual
python src/data_monitor.py --action check

# Trigger manual con threshold personalizado  
python src/data_monitor.py --action check --threshold 50

# Marcar reentrenamiento como completado
python src/data_monitor.py --action mark-completed

# Ver historial
python src/data_monitor.py --action history
```

### GitHub Actions Variables:

- `RETRAIN_THRESHOLD`: Mínimas filas nuevas (default: 100)
- `FORCE_RETRAIN`: Forzar reentrenamiento (true/false)
- Trigger manual desde GitHub con parámetros personalizables

## Docker

### Construir imagen:

```bash
docker build -t fraud-detection-api .
```

### Ejecutar contenedor:

```bash
docker run -p 8000:8000 fraud-detection-api
# API disponible en http://localhost:8000
```

### Docker Compose (próximamente):

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "8000:8000"
  scheduler:
    build: .
    command: python src/scheduler.py
```

## Testing

### Suite básica:
```bash
python test_api.py
# 4/4 tests pasando
```

### Suite avanzada:
```bash
python test_api_advanced.py  
# 6/6 tests pasando (incluye performance y edge cases)
```

### Tests incluidos:
- Health checks
- Predicciones válidas e inválidas  
- Batch processing
- Performance (concurrencia)
- Edge cases y validación de datos
- Integración con datos reales

## Dataset y Modelo

### Dataset: 
- **Origen:** Kaggle creditcardfraud
- **Tamaño:** 10,000 transacciones (de 284k originales)
- **Features:** 7 columnas (Time, V1, V2, V4, V11, Amount, Class)
- **Balance:** 99.62% legítimas, 0.38% fraudulentas

### Modelo:
- **Algoritmo:** RandomForest (100 estimators)  
- **Preprocessing:** StandardScaler pipeline
- **Performance:** AUC 0.9998 (test), 0.9662 (CV)
- **Interpretabilidad:** Feature importance disponible

### Métricas de calidad:
```python
# Resultados del modelo actual:
Test AUC: 0.9998
Cross-validation AUC: 0.9662 ± 0.0071
False Positives: Minimizados para reducir fricción
```

## Configuración Avanzada

### **Variables de entorno:**
```bash
# .env (opcional)
MODEL_PATH=models/fraud_model.joblib
DATA_PATH=data/
API_HOST=0.0.0.0  
API_PORT=8000
LOG_LEVEL=INFO
```

### **Personalizar reentrenamiento:**
```python
# src/config.py
RETRAIN_CONFIG = {
    'min_auc': 0.85,           # AUC mínimo aceptable
    'max_degradation': 0.05,   # Máxima degradación permitida
    'min_new_rows': 100,       # Mínimas filas para trigger  
    'backup_models': True,     # Backup automático
    'run_tests': True          # Tests post-entrenamiento
}
```

## 📄 Licencia

MIT License - ver archivo `LICENSE` para detalles.

---

## 📞 Contacto y Soporte

- **Documentación:** Ver `TEST_RESULTS.md` para detalles técnicos
- **Issues:** Usa GitHub Issues para reportar bugs
- **MLOps Best Practices:** Este proyecto sigue patrones estándar de la industria

**🎯 ¡Proyecto listo para producción con CI/CD automático!**
