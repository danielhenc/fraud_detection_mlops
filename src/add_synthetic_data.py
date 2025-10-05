"""
Script para agregar filas sintéticas a los datos de entrenamiento.
Genera datos aleatorios basados en las estadísticas del dataset existente.
"""
import pandas as pd
import numpy as np
import argparse
from pathlib import Path

def analyze_existing_data():
    """Analiza las estadísticas del dataset existente."""
    X_train = pd.read_csv('data/X_train.csv')
    y_train = pd.read_csv('data/y_train.csv')
    
    # Estadísticas por clase
    fraud_mask = y_train.iloc[:, 0] == 1
    legit_mask = y_train.iloc[:, 0] == 0
    
    fraud_stats = X_train[fraud_mask].describe()
    legit_stats = X_train[legit_mask].describe()
    
    fraud_rate = fraud_mask.sum() / len(y_train)
    
    print(f"Análisis del dataset existente:")
    print(f"- Total filas: {len(X_train)}")
    print(f"- Transacciones fraudulentas: {fraud_mask.sum()} ({fraud_rate:.4f})")
    print(f"- Transacciones legítimas: {legit_mask.sum()} ({1-fraud_rate:.4f})")
    
    return fraud_stats, legit_stats, fraud_rate

def generate_synthetic_rows(n_rows, fraud_stats, legit_stats, fraud_rate):
    """Genera filas sintéticas basadas en estadísticas existentes."""
    
    # Determinar cuántas fraudulentas vs legítimas
    n_fraud = int(n_rows * fraud_rate)
    n_legit = n_rows - n_fraud
    
    print(f"Generando {n_rows} filas: {n_fraud} fraudulentas, {n_legit} legítimas")
    
    synthetic_X = []
    synthetic_y = []
    
    # Generar transacciones fraudulentas
    for _ in range(n_fraud):
        row = {}
        for col in fraud_stats.columns:
            mean = fraud_stats.loc['mean', col]
            std = fraud_stats.loc['std', col]
            # Generar valor con distribución normal
            value = np.random.normal(mean, std)
            row[col] = value
        synthetic_X.append(row)
        synthetic_y.append(1)
    
    # Generar transacciones legítimas
    for _ in range(n_legit):
        row = {}
        for col in legit_stats.columns:
            mean = legit_stats.loc['mean', col]
            std = legit_stats.loc['std', col]
            # Generar valor con distribución normal
            value = np.random.normal(mean, std)
            row[col] = value
        synthetic_X.append(row)
        synthetic_y.append(0)
    
    return pd.DataFrame(synthetic_X), pd.Series(synthetic_y)

def add_synthetic_data(n_rows):
    """Agrega datos sintéticos a los archivos de entrenamiento."""
    
    # Verificar que existan los archivos
    if not Path('data/X_train.csv').exists() or not Path('data/y_train.csv').exists():
        print("Error: No se encuentran los archivos X_train.csv o y_train.csv")
        return
    
    # Analizar datos existentes
    fraud_stats, legit_stats, fraud_rate = analyze_existing_data()
    
    # Generar datos sintéticos
    np.random.seed(42)  # Para reproducibilidad
    synthetic_X, synthetic_y = generate_synthetic_rows(n_rows, fraud_stats, legit_stats, fraud_rate)
    
    # Cargar datos existentes
    existing_X = pd.read_csv('data/X_train.csv')
    existing_y = pd.read_csv('data/y_train.csv')
    
    # Combinar datos
    new_X = pd.concat([existing_X, synthetic_X], ignore_index=True)
    synthetic_y_df = pd.DataFrame(synthetic_y, columns=existing_y.columns)
    new_y = pd.concat([existing_y, synthetic_y_df], ignore_index=True)
    
    # Guardar archivos actualizados
    new_X.to_csv('data/X_train.csv', index=False)
    new_y.to_csv('data/y_train.csv', index=False)
    
    print(f"\n✅ Datos actualizados:")
    print(f"- Filas anteriores: {len(existing_X)}")
    print(f"- Filas nuevas: {n_rows}")
    print(f"- Total filas: {len(new_X)}")
    
    # Verificar nueva distribución
    new_fraud_rate = (new_y.iloc[:, 0] == 1).sum() / len(new_y)
    print(f"- Nueva tasa de fraude: {new_fraud_rate:.4f}")

def main():
    parser = argparse.ArgumentParser(description='Agregar filas sintéticas a los datos de entrenamiento')
    parser.add_argument('n_rows', type=int, help='Número de filas a agregar')
    parser.add_argument('--preview', action='store_true', help='Solo mostrar preview sin guardar')
    
    args = parser.parse_args()
    
    if args.preview:
        print("=== PREVIEW MODE ===")
        fraud_stats, legit_stats, fraud_rate = analyze_existing_data()
        n_fraud = int(args.n_rows * fraud_rate)
        n_legit = args.n_rows - n_fraud
        print(f"\nSe agregarían:")
        print(f"- {args.n_rows} filas total")
        print(f"- {n_fraud} fraudulentas ({fraud_rate:.4f})")
        print(f"- {n_legit} legítimas ({1-fraud_rate:.4f})")
    else:
        print(f"=== AGREGANDO {args.n_rows} FILAS SINTÉTICAS ===")
        add_synthetic_data(args.n_rows)

if __name__ == "__main__":
    main()