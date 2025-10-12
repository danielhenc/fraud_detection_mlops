# Docker Setup para Fraud Detection MLOps

Este proyecto incluye configuración completa de Docker para desarrollo y producción.

## Estructura Docker

```
fraud_detection_mlops/
├── Dockerfile                 # Imagen principal con multi-stage build
├── docker-compose.yml         # Stack completo con monitoreo
├── docker-compose.dev.yml     # Solo para desarrollo
├── .dockerignore             # Optimización del contexto de build
└── monitoring/               # Configuraciones de monitoreo
    ├── prometheus.yml
    └── grafana/
        ├── datasources/
        └── dashboards/
```

## Comandos Principales

### Desarrollo Rápido
```bash
# Solo la API para desarrollo
docker-compose -f docker-compose.dev.yml up --build

# Con recarga automática de código
docker-compose -f docker-compose.dev.yml up fraud-api-dev
```

### Stack Completo con Monitoreo
```bash
# Levantar todo el stack
docker-compose up --build

# Solo servicios específicos
docker-compose up fraud-api prometheus grafana
```

### Entrenamiento Manual
```bash
# Ejecutar reentrenamiento
docker-compose run --rm model-trainer
```

## Servicios Disponibles

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **fraud-api** | 8000 | API principal de detección de fraude |
| **prometheus** | 9090 | Métricas y monitoreo |
| **grafana** | 3000 | Dashboards (admin/admin123) |
| **redis** | 6379 | Caché para escalabilidad |
| **postgres-test** | 5432 | BD para testing (solo dev) |

## Endpoints Principales

- **API Health**: http://localhost:8000/health
- **Predicción**: http://localhost:8000/predict
- **Métricas**: http://localhost:8000/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## Optimizaciones Incluidas

### Dockerfile
- ✅ Multi-stage build para imagen más pequeña
- ✅ Usuario no-root para seguridad
- ✅ Healthcheck automático
- ✅ Caché de dependencias optimizado

### Docker Compose
- ✅ Redes aisladas
- ✅ Volúmenes persistentes
- ✅ Restart policies
- ✅ Profiles para diferentes entornos

### Monitoreo
- ✅ Prometheus para métricas
- ✅ Grafana para visualización
- ✅ Configuración automática de datasources

## Actualización Automática de Modelos

### 🔄 **Flujo de Actualización Automática**

Cuando GitHub Actions reentrena el modelo:

1. **Build automático**: Se construye nueva imagen Docker
2. **Hot reload**: API detecta cambios y recarga modelo automáticamente  
3. **Notificación**: GitHub Actions notifica a contenedores running
4. **Verificación**: Se confirma que el nuevo modelo está cargado

### 📡 **Endpoints de Control**

```bash
# Verificar estado del modelo
curl http://localhost:8000/health

# Recargar modelo manualmente
curl -X POST http://localhost:8000/reload-model

# Verificar predicción
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"Time":0,"V1":-1.36,"V2":-0.07,"V4":2.54,"V11":1.18,"Amount":149.62}'
```

### 🚀 **Script de Deployment**

```bash
# Deployment automático en desarrollo
./deploy.sh development

# Deployment en producción  
./deploy.sh production

# Forzar rebuild de imagen
./deploy.sh development --force-rebuild
```

## Comandos Útiles

```bash
# Ver logs de la API
docker-compose logs -f fraud-api

# Rebuild solo la API
docker-compose build fraud-api

# Verificar modelo cargado
curl http://localhost:8000/health | jq .model_metadata

# Recargar modelo tras cambios
curl -X POST http://localhost:8000/reload-model

# Limpiar todo
docker-compose down -v --rmi all

# Solo desarrollo
docker-compose -f docker-compose.dev.yml up
```

## Variables de Entorno

### Desarrollo
```env
ENV=development
LOG_LEVEL=DEBUG
RELOAD=true
```

### Producción
```env
ENV=production
LOG_LEVEL=INFO
MODEL_PATH=/app/models/fraud_model.joblib
```

## Troubleshooting

### La API no arranca
```bash
# Verificar logs
docker-compose logs fraud-api

# Verificar healthcheck
docker-compose ps
```

### Problemas de permisos
```bash
# Reconstruir con permisos correctos
docker-compose build --no-cache fraud-api
```

### Datos no actualizados
```bash
# Forzar recreación de volúmenes
docker-compose down -v
docker-compose up --build
```