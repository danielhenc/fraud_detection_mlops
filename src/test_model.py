import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model import FraudDetectionModel
import pandas as pd
import numpy as np

# Test de carga
model = FraudDetectionModel()
model.load_model()
print('Modelo carga correctamente')

# Test de predicción
test_data = pd.DataFrame({
    'Time': [0.0], 'V1': [-1.359807], 'V2': [-0.072781], 
    'V4': [2.536347], 'V11': [1.175480], 'Amount': [149.62]
})

pred = model.predict(test_data)
prob = model.predict_proba(test_data)

print(f'Predicción: {pred[0]}, Probabilidad: {prob[0]:.4f}')
print('Todos los tests pasaron')