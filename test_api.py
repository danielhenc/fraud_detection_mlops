"""
Script para probar todos los endpoints de la API de detección de fraude.
"""
import requests
import json
import time
import pandas as pd

API_BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Prueba el endpoint de health check."""
    print("=== PROBANDO /health ===")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False

def test_root_endpoint():
    """Prueba el endpoint raíz."""
    print("\n=== PROBANDO / ===")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False

def test_model_info_endpoint():
    """Prueba el endpoint de información del modelo."""
    print("\n=== PROBANDO /model/info ===")
    try:
        response = requests.get(f"{API_BASE_URL}/model/info", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False

def test_single_prediction():
    """Prueba el endpoint de predicción individual."""
    print("\n=== PROBANDO /predict ===")
    
    # Datos de ejemplo (transacción normal)
    normal_transaction = {
        "Time": 0.0,
        "V1": -1.359807,
        "V2": -0.072781,
        "V4": 2.536347,
        "V11": 1.175480,
        "Amount": 149.62
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=normal_transaction,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        
        if response.status_code == 200:
            print(f"  Fraude detectado: {result['is_fraud']}")
            print(f"  Probabilidad: {result['fraud_probability']:.4f}")
            print(f"  Nivel de riesgo: {result['risk_score']}")
        
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False

def test_batch_prediction():
    """Prueba el endpoint de predicción en lote."""
    print("\n=== PROBANDO /predict/batch ===")
    
    # Lote de transacciones de prueba
    batch_transactions = {
        "transactions": [
            {
                "Time": 0.0,
                "V1": -1.359807,
                "V2": -0.072781,
                "V4": 2.536347,
                "V11": 1.175480,
                "Amount": 149.62
            },
            {
                "Time": 3600.0,
                "V1": -3.249037,
                "V2": 1.827126,
                "V4": -5.237547,
                "V11": 2.345895,
                "Amount": 2125.87
            },
            {
                "Time": 7200.0,
                "V1": 1.234567,
                "V2": -2.456789,
                "V4": 0.987654,
                "V11": -1.543210,
                "Amount": 50.25
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict/batch",
            json=batch_transactions,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            summary = result['batch_summary']
            print(f"\n  RESUMEN DEL LOTE:")
            print(f"  Total transacciones: {summary['total_transactions']}")
            print(f"  Fraudes detectados: {summary['fraud_detected']}")
            print(f"  Tasa de fraude: {summary['fraud_rate']:.4f}")
        
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False

def load_real_data_test():
    """Prueba con datos reales del dataset de test."""
    print("\n=== PROBANDO CON DATOS REALES ===")
    
    try:
        # Cargar algunos datos de test (path correcto)
        X_test = pd.read_csv('data/X_test.csv').head(5)
        print(f"Cargados {len(X_test)} ejemplos de test")
        
        for i, row in X_test.iterrows():
            transaction = row.to_dict()
            print(f"\n  Transacción {i+1}:")
            
            response = requests.post(
                f"{API_BASE_URL}/predict",
                json=transaction,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"    Fraude: {result['is_fraud']}, Prob: {result['fraud_probability']:.4f}, Riesgo: {result['risk_score']}")
            else:
                print(f"    Error: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"Error cargando datos reales: {e}")
        return False

def run_all_tests():
    """Ejecuta todas las pruebas."""
    print("🧪 INICIANDO PRUEBAS DE LA API")
    print("=" * 50)
    
    # Esperar un poco para asegurar que la API esté lista
    print("Esperando 2 segundos para que la API esté lista...")
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Root Endpoint", test_root_endpoint),
        ("Model Info", test_model_info_endpoint),
        ("Single Prediction", test_single_prediction),
        ("Batch Prediction", test_batch_prediction),
        ("Real Data Test", load_real_data_test)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 RESULTADOS: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
    else:
        print("⚠️  Algunas pruebas fallaron")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()