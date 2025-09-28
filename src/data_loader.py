"""
Script para cargar y procesar el dataset de fraude de Kaggle.
Usa solo 7 columnas y 10000 filas para entrenar.
"""
import pandas as pd
import numpy as np
import kagglehub
from sklearn.model_selection import train_test_split
import os

def load_and_process_data():
    """Carga el dataset de Kaggle y lo procesa para usar solo 7 columnas y 10k filas."""
    print("Descargando dataset de Kaggle...")
    
    # Descargar dataset de fraude de tarjetas de crédito
    path = kagglehub.dataset_download("mlg-ulb/creditcardfraud")
    print(f"Dataset descargado en: {path}")
    
    # Cargar el CSV
    csv_file = os.path.join(path, "creditcard.csv")
    df = pd.read_csv(csv_file)
    
    print(f"Dataset original shape: {df.shape}")
    print(f"Columnas disponibles: {list(df.columns)}")
    
    # Seleccionar 7 columnas más relevantes (incluyendo Amount, Time y Class)
    # y algunas V features que suelen ser importantes
    selected_columns = ['Time', 'V1', 'V2', 'V4', 'V11', 'Amount', 'Class']
    
    # Filtrar por las columnas seleccionadas
    df_subset = df[selected_columns].copy()
    
    # Tomar solo 10k filas
    df_subset = df_subset.head(10000)
    
    print(f"Dataset procesado shape: {df_subset.shape}")
    print(f"Distribución de clases:")
    print(df_subset['Class'].value_counts())
    
    # Guardar el dataset procesado
    output_path = os.path.join('data', 'fraud_data_processed.csv')
    df_subset.to_csv(output_path, index=False)
    print(f"Dataset guardado en: {output_path}")
    
    return df_subset

def split_data(df):
    """Divide el dataset en train/test."""
    X = df.drop('Class', axis=1)
    y = df['Class']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Train shape: {X_train.shape}")
    print(f"Test shape: {X_test.shape}")
    print(f"Train fraud rate: {y_train.mean():.4f}")
    print(f"Test fraud rate: {y_test.mean():.4f}")
    
    return X_train, X_test, y_train, y_test

if __name__ == "__main__":
    # Asegurarse de que existe la carpeta data
    os.makedirs('data', exist_ok=True)
    
    # Cargar y procesar datos
    df = load_and_process_data()
    
    # Dividir datos
    X_train, X_test, y_train, y_test = split_data(df)
    
    # Guardar splits
    X_train.to_csv('data/X_train.csv', index=False)
    X_test.to_csv('data/X_test.csv', index=False)
    y_train.to_csv('data/y_train.csv', index=False)
    y_test.to_csv('data/y_test.csv', index=False)
    
    print("Dataset preparado y splits guardados!")