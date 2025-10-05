import sys
import os

# Agregar directorio actual al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

old_auc = float(os.environ.get('OLD_AUC', '0.0'))
new_auc = float(os.environ.get('NEW_AUC', '0.0'))
min_auc = float(os.environ.get('MIN_AUC', '0.85'))

passes_minimum = new_auc >= min_auc
degradation_acceptable = new_auc >= (old_auc * 0.95) if old_auc > 0 else True

print(f"Pasa AUC mínimo ({min_auc}): {passes_minimum}")
print(f"Degradación aceptable (<5%): {degradation_acceptable}")

if passes_minimum and degradation_acceptable:
    print("MODELO VALIDADO - Apto para despliegue")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write('model_valid=true\n')
    sys.exit(0)
else:
    print("MODELO RECHAZADO - No pasa validación")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write('model_valid=false\n')
    sys.exit(1)