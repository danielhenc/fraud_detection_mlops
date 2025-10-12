#!/bin/bash

# Script para deployment y actualización de contenedores con nuevo modelo
# Uso: ./deploy.sh [production|development] [--force-rebuild]

set -e

ENV=${1:-development}
FORCE_REBUILD=${2:-}

MODEL_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "latest")
IMAGE_NAME="fraud-detection"
CONTAINER_NAME="fraud-api-${ENV}"

echo "=== Deployment Script para Fraud Detection API ==="
echo "Entorno: $ENV"
echo "Versión del modelo: $MODEL_VERSION"
echo "==============================================="

# Función para verificar si el contenedor está corriendo
check_container_running() {
    if docker ps | grep -q "$CONTAINER_NAME"; then
        return 0
    else
        return 1
    fi
}

# Función para notificar recarga de modelo
notify_model_reload() {
    local endpoint="http://localhost:8000"
    
    echo "Esperando que la API esté disponible..."
    for i in {1..30}; do
        if curl -f "$endpoint/health" >/dev/null 2>&1; then
            echo "API disponible, solicitando recarga del modelo..."
            if curl -X POST "$endpoint/reload-model" -H "Content-Type: application/json"; then
                echo "✅ Modelo recargado exitosamente"
                return 0
            else
                echo "❌ Error recargando modelo"
                return 1
            fi
        fi
        sleep 2
    done
    
    echo "❌ Timeout esperando que la API esté disponible"
    return 1
}

# Construir imagen si es necesario
if [ "$FORCE_REBUILD" = "--force-rebuild" ] || ! docker images | grep -q "$IMAGE_NAME:$MODEL_VERSION"; then
    echo "🔨 Construyendo imagen Docker..."
    docker build -t "$IMAGE_NAME:$MODEL_VERSION" .
    docker tag "$IMAGE_NAME:$MODEL_VERSION" "$IMAGE_NAME:latest"
    echo "✅ Imagen construida: $IMAGE_NAME:$MODEL_VERSION"
else
    echo "ℹ️  Usando imagen existente: $IMAGE_NAME:$MODEL_VERSION"
fi

# Estrategia según entorno
case $ENV in
    "development")
        echo "🚀 Desplegando en modo desarrollo..."
        
        # Si hay contenedor corriendo, intentar recarga primero
        if check_container_running; then
            echo "📡 Contenedor existente detectado, intentando recarga de modelo..."
            if notify_model_reload; then
                echo "✅ Deployment completado via model reload"
                exit 0
            else
                echo "⚠️  Recarga falló, reiniciando contenedor..."
                docker-compose -f docker-compose.dev.yml down
            fi
        fi
        
        # Levantar con docker-compose
        docker-compose -f docker-compose.dev.yml up -d --build
        echo "✅ Contenedor de desarrollo iniciado"
        ;;
        
    "production")
        echo "🚀 Desplegando en modo producción..."
        
        # Si hay contenedor corriendo, intentar recarga primero
        if check_container_running; then
            echo "📡 Contenedor existente detectado, intentando recarga de modelo..."
            if notify_model_reload; then
                echo "✅ Deployment completado via model reload"
                exit 0
            else
                echo "⚠️  Recarga falló, realizando rolling update..."
            fi
        fi
        
        # Rolling update con docker-compose
        docker-compose down
        docker-compose up -d --build
        echo "✅ Contenedor de producción actualizado"
        ;;
        
    *)
        echo "❌ Entorno no válido. Use: development o production"
        exit 1
        ;;
esac

# Verificar que el deployment fue exitoso
echo "🔍 Verificando deployment..."
if notify_model_reload; then
    echo "✅ Deployment verificado exitosamente"
    echo "🌐 API disponible en: http://localhost:8000"
    echo "📊 Health check: http://localhost:8000/health"
else
    echo "❌ Deployment falló la verificación"
    exit 1
fi

echo "✅ Deployment completado para entorno: $ENV"