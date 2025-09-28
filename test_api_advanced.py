"""
Tests adicionales para validar performance, edge cases y robustez de la API.
"""
import requests
import json
import time
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

API_BASE_URL = "http://localhost:8000"

def test_invalid_data():
    """Prueba con datos inválidos."""
    print("\n=== PROBANDO DATOS INVÁLIDOS ===")
    
    # Datos faltantes
    invalid_transactions = [
        {"Time": 0.0, "V1": -1.359807},  # Faltan campos
        {"Time": "invalid", "V1": -1.359807, "V2": -0.072781, "V4": 2.536347, "V11": 1.175480, "Amount": 149.62},  # Tipo inválido
        {"Time": None, "V1": -1.359807, "V2": -0.072781, "V4": 2.536347, "V11": 1.175480, "Amount": 149.62},  # Valor nulo
    ]
    
    passed = 0
    for i, invalid_tx in enumerate(invalid_transactions, 1):
        print(f"  Caso inválido {i}:")
        try:
            response = requests.post(
                f"{API_BASE_URL}/predict",
                json=invalid_tx,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            print(f"    Status: {response.status_code}")
            if response.status_code == 422:  # Validation error esperado
                print(f"    ✅ Error de validación detectado correctamente")
                passed += 1
            else:
                print(f"    ❌ Debería haber dado error 422")
        except Exception as e:
            print(f"    Error: {e}")
    
    return passed == len(invalid_transactions)

def test_extreme_values():
    """Prueba con valores extremos."""
    print("\n=== PROBANDO VALORES EXTREMOS ===")
    
    extreme_transactions = [
        # Valores muy grandes
        {"Time": 999999.0, "V1": 1000.0, "V2": -1000.0, "V4": 500.0, "V11": -500.0, "Amount": 100000.0},
        # Valores muy pequeños
        {"Time": 0.001, "V1": 0.00001, "V2": -0.00001, "V4": 0.0, "V11": 0.0, "Amount": 0.01},
        # Valores negativos en Amount (edge case)
        {"Time": 100.0, "V1": -2.0, "V2": 1.5, "V4": -1.0, "V11": 0.5, "Amount": -50.0},
    ]
    
    passed = 0
    for i, tx in enumerate(extreme_transactions, 1):
        print(f"  Caso extremo {i}:")
        try:
            response = requests.post(
                f"{API_BASE_URL}/predict",
                json=tx,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                print(f"    ✅ Procesado: Fraude={result['is_fraud']}, Prob={result['fraud_probability']:.4f}")
                passed += 1
            else:
                print(f"    ❌ Error: {response.status_code}")
        except Exception as e:
            print(f"    Error: {e}")
    
    return passed == len(extreme_transactions)

def test_performance_load():
    """Prueba de carga con múltiples requests concurrentes."""
    print("\n=== PROBANDO PERFORMANCE ===")
    
    # Transacción base
    base_transaction = {
        "Time": 0.0,
        "V1": -1.359807,
        "V2": -0.072781,
        "V4": 2.536347,
        "V11": 1.175480,
        "Amount": 149.62
    }
    
    def make_request(i):
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/predict",
                json=base_transaction,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            end_time = time.time()
            
            return {
                'id': i,
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'success': response.status_code == 200
            }
        except Exception as e:
            return {
                'id': i,
                'status_code': 0,
                'response_time': 0,
                'success': False,
                'error': str(e)
            }
    
    # Ejecutar 20 requests concurrentes
    num_requests = 20
    print(f"  Ejecutando {num_requests} requests concurrentes...")
    
    start_total = time.time()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, i) for i in range(num_requests)]
        results = [future.result() for future in as_completed(futures)]
    end_total = time.time()
    
    # Análisis de resultados
    successful = sum(1 for r in results if r['success'])
    response_times = [r['response_time'] for r in results if r['success']]
    
    print(f"  ✅ Requests exitosos: {successful}/{num_requests}")
    print(f"  📊 Tiempo total: {end_total - start_total:.2f}s")
    if response_times:
        print(f"  ⏱️  Tiempo respuesta promedio: {np.mean(response_times):.3f}s")
        print(f"  ⏱️  Tiempo respuesta máximo: {np.max(response_times):.3f}s")
        print(f"  ⏱️  Tiempo respuesta mínimo: {np.min(response_times):.3f}s")
    
    return successful >= num_requests * 0.8  # 80% success rate mínimo

def test_large_batch():
    """Prueba con lote grande de transacciones."""
    print("\n=== PROBANDO LOTE GRANDE ===")
    
    # Generar 50 transacciones sintéticas
    np.random.seed(42)
    large_batch = {
        "transactions": []
    }
    
    for i in range(50):
        tx = {
            "Time": np.random.uniform(0, 86400),  # 24 horas
            "V1": np.random.normal(0, 2),
            "V2": np.random.normal(0, 2),
            "V4": np.random.normal(0, 2),
            "V11": np.random.normal(0, 2),
            "Amount": np.random.lognormal(3, 1.5)
        }
        large_batch["transactions"].append(tx)
    
    print(f"  Enviando lote de {len(large_batch['transactions'])} transacciones...")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/predict/batch",
            json=large_batch,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            summary = result['batch_summary']
            print(f"  ✅ Procesado exitosamente en {end_time - start_time:.2f}s")
            print(f"    Transacciones: {summary['total_transactions']}")
            print(f"    Fraudes detectados: {summary['fraud_detected']}")
            print(f"    Tiempo promedio por transacción: {(end_time - start_time)/summary['total_transactions']*1000:.1f}ms")
            return True
        else:
            print(f"  ❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  Error: {e}")
        return False

def run_advanced_tests():
    """Ejecuta todos los tests avanzados."""
    print("🔬 INICIANDO TESTS AVANZADOS DE LA API")
    print("=" * 60)
    
    advanced_tests = [
        ("Datos Inválidos", test_invalid_data),
        ("Valores Extremos", test_extreme_values),
        ("Performance Concurrente", test_performance_load),
        ("Lote Grande", test_large_batch)
    ]
    
    passed = 0
    total = len(advanced_tests)
    
    for test_name, test_func in advanced_tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print(f"\n{'='*60}")
    print(f"🎯 RESULTADOS TESTS AVANZADOS: {passed}/{total} pasaron")
    
    if passed == total:
        print("🚀 ¡TODOS LOS TESTS AVANZADOS PASARON!")
    else:
        print("⚠️  Algunos tests avanzados fallaron")
    
    return passed == total

if __name__ == "__main__":
    run_advanced_tests()