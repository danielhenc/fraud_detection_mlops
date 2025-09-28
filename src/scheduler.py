"""
Scheduler para reentrenamiento automático usando schedule.
Simula un cron job que ejecuta reentrenamiento cada día.
"""
import schedule
import time
import logging
from datetime import datetime
import os

from retrain import run_retraining

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def scheduled_retraining():
    """Función que se ejecuta en el schedule."""
    logger.info("=== REENTRENAMIENTO PROGRAMADO INICIADO ===")
    
    try:
        result = run_retraining()
        
        if result['status'] == 'success':
            logger.info("Reentrenamiento completado exitosamente")
        elif result['status'] == 'skipped':
            logger.info("Reentrenamiento omitido - no necesario")
        else:
            logger.warning(f"Reentrenamiento falló: {result['status']}")
            
    except Exception as e:
        logger.error(f"Error en reentrenamiento programado: {e}")
    
    logger.info("=== REENTRENAMIENTO PROGRAMADO FINALIZADO ===")

def start_scheduler():
    """Inicia el scheduler."""
    # Crear directorio de logs si no existe
    os.makedirs('logs', exist_ok=True)
    
    # Programar reentrenamiento diario a las 2:00 AM
    schedule.every().day.at("02:00").do(scheduled_retraining)
    
    # Para testing, también cada 30 minutos (comentar en producción)
    # schedule.every(30).minutes.do(scheduled_retraining)
    
    logger.info("Scheduler iniciado - Reentrenamiento programado para las 2:00 AM diario")
    logger.info("Presiona Ctrl+C para detener el scheduler")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Scheduler detenido por el usuario")

if __name__ == "__main__":
    start_scheduler()