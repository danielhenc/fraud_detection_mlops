# Despliegue en Render - Fraud Detection API

Este documento explica cómo desplegar la API de detección de fraude en Render.

## Configuración Automática

El proyecto incluye un archivo `render.yaml` que configura automáticamente el despliegue:

- **Tipo**: Web Service con Docker
- **Plan**: Starter (gratuito)
- **Health Check**: `/health`
- **Puerto**: Dinámico (asignado por Render)
- **Auto Deploy**: Habilitado

## Pasos para Desplegar

### 1. Preparar el Repositorio
```bash
# Asegurar que todos los cambios estén commiteados
git add .
git commit -m "Preparar para despliegue en Render"
git push origin main
```

### 2. Crear Servicio en Render
1. Ve a [render.com](https://render.com) y crea una cuenta
2. Click en "New +" → "Web Service"
3. Conecta tu repositorio GitHub `danielhenc/fraud_detection_mlops`
4. Render detectará automáticamente el `render.yaml`

### 3. Variables de Entorno (Automáticas)
Las siguientes variables se configuran automáticamente:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `PORT` | Dinámico | Puerto asignado por Render |
| `ENV` | production | Entorno de producción |
| `LOG_LEVEL` | INFO | Nivel de logging |
| `ENABLE_MODEL_WATCHER` | false | Desactivado en producción |

## Características del Despliegue

### ✅ **Optimizaciones para Producción**
- Logging en formato JSON estructurado
- Model watcher deshabilitado para mejor performance
- Health checks automáticos cada 30s
- Reinicio automático en caso de falla

### ✅ **Configuración Dinámica**
- Puerto adaptativo (Render asigna automáticamente)
- Variables de entorno centralizadas
- Configuración diferenciada por entorno

### ✅ **Persistencia de Modelos**
- Modelo inicial incluido en la imagen Docker
- Logs persistentes en disco de 1GB
- Archivos de configuración versionados

## Endpoints Disponibles

Una vez desplegado, la API estará disponible en tu URL de Render:

```bash
# Health check
GET https://tu-app.onrender.com/health

# Predicción individual
POST https://tu-app.onrender.com/predict
Content-Type: application/json
{
  "Time": 0.0,
  "V1": -1.359807,
  "V2": -0.072781,
  "V4": 2.536347,
  "V11": 1.175480,
  "Amount": 149.62
}

# Información del modelo
GET https://tu-app.onrender.com/model/info

# Recarga manual del modelo (si es necesario)
POST https://tu-app.onrender.com/reload-model
```

## Monitoreo y Logs

### Ver Logs en Tiempo Real
```bash
# En el dashboard de Render
Dashboard → tu-servicio → Logs
```

### Métricas Importantes
- **Response Time**: < 500ms típico
- **Memory Usage**: ~200MB
- **CPU Usage**: Bajo en reposo
- **Health Check**: Debe ser 200 OK

## Limitaciones del Plan Gratuito

- **Sleep after 15 min**: Se "duerme" sin actividad
- **Cold Start**: ~30s para "despertar"
- **Monthly Hours**: 750h/mes gratuitas
- **Bandwidth**: 100GB/mes
- **Build Time**: 500 min/mes

## Actualizaciones Automáticas

### Reentrenamiento de Modelos
1. GitHub Actions reentrena el modelo
2. Se hace commit del nuevo modelo
3. Render detecta el cambio y redespliega automáticamente
4. El nuevo modelo estará disponible en ~2-3 minutos

### Workflow de CI/CD
```
Cambio en datos → GitHub Actions → Nuevo modelo → 
Commit → Render Auto-Deploy → API actualizada
```

## Troubleshooting

### La API no responde
```bash
# Verificar logs
curl https://tu-app.onrender.com/health

# Si no responde, podría estar "dormida"
# Hacer una request para "despertarla"
```

### Modelo no se carga
```bash
# Verificar que el modelo existe en el repo
curl https://tu-app.onrender.com/model/info

# Si falla, verificar que fraud_model.joblib está en models/
```

### Performance lento
- **Cold start**: Normal en plan gratuito
- **Upgrade a plan pagado** para mejor performance
- **Keep-alive requests** para evitar sleep

## URLs de Ejemplo

Una vez desplegado, tu API estará disponible en:
- **Health**: `https://fraud-detection-api-xxx.onrender.com/health`
- **Docs**: `https://fraud-detection-api-xxx.onrender.com/docs`
- **Predict**: `https://fraud-detection-api-xxx.onrender.com/predict`

## Siguiente Paso: Conectar con Frontend

Una vez que la API esté funcionando en Render, puedes:
1. Crear un frontend simple (HTML/JS)
2. Desplegar el frontend en Netlify/Vercel
3. Conectar ambos servicios para una demo completa

¡Tu API de MLOps está lista para producción! 🚀