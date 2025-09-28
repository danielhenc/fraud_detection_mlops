"""
Data Monitor para detectar cambios en los datasets de entrenamiento.
Compara tamaño actual vs registrado y determina si se necesita reentrenamiento.
"""
import pandas as pd
import os
import json
from datetime import datetime
import sys

class DataMonitor:
    def __init__(self, data_dir='data', threshold=100, state_file='data_state.json'):
        self.data_dir = data_dir
        self.threshold = threshold
        self.state_file = state_file
        self.current_state = self.load_state()
    
    def load_state(self):
        """Carga el estado anterior del monitor."""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'last_check': None,
            'X_train_rows': 0,
            'y_train_rows': 0,
            'last_retrain': None,
            'retrain_count': 0
        }
    
    def save_state(self):
        """Guarda el estado actual del monitor."""
        with open(self.state_file, 'w') as f:
            json.dump(self.current_state, f, indent=2)
    
    def get_current_data_size(self):
        """Obtiene el tamaño actual de los datasets."""
        X_train_path = os.path.join(self.data_dir, 'X_train.csv')
        y_train_path = os.path.join(self.data_dir, 'y_train.csv')
        
        if not os.path.exists(X_train_path) or not os.path.exists(y_train_path):
            print("Warning: Training data files not found")
            return 0, 0
        
        X_rows = len(pd.read_csv(X_train_path))
        y_rows = len(pd.read_csv(y_train_path))
        
        return X_rows, y_rows
    
    def check_for_new_data(self):
        """Verifica si hay suficientes nuevos datos para reentrenamiento."""
        current_X_rows, current_y_rows = self.get_current_data_size()
        
        previous_X_rows = self.current_state.get('X_train_rows', 0)
        previous_y_rows = self.current_state.get('y_train_rows', 0)
        
        new_X_rows = current_X_rows - previous_X_rows
        new_y_rows = current_y_rows - previous_y_rows
        
        print(f"Estado actual:")
        print(f"  X_train: {current_X_rows} filas (nuevas: {new_X_rows})")
        print(f"  y_train: {current_y_rows} filas (nuevas: {new_y_rows})")
        print(f"  Threshold: {self.threshold} nuevas filas")
        
        needs_retrain = (new_X_rows >= self.threshold and new_y_rows >= self.threshold)
        
        # Actualizar estado
        self.current_state.update({
            'last_check': datetime.now().isoformat(),
            'X_train_rows': current_X_rows,
            'y_train_rows': current_y_rows
        })
        
        if needs_retrain:
            print(f"✅ REENTRENAMIENTO NECESARIO: {max(new_X_rows, new_y_rows)} nuevas filas >= {self.threshold}")
        else:
            print(f"⏳ Reentrenamiento no necesario: {max(new_X_rows, new_y_rows)} nuevas filas < {self.threshold}")
        
        return needs_retrain, {
            'new_X_rows': new_X_rows,
            'new_y_rows': new_y_rows,
            'current_X_rows': current_X_rows,
            'current_y_rows': current_y_rows,
            'threshold': self.threshold
        }
    
    def mark_retrain_completed(self):
        """Marca que se completó un reentrenamiento."""
        self.current_state.update({
            'last_retrain': datetime.now().isoformat(),
            'retrain_count': self.current_state.get('retrain_count', 0) + 1
        })
        self.save_state()
        print(f"✅ Reentrenamiento #{self.current_state['retrain_count']} completado")
    
    def get_retrain_history(self):
        """Obtiene historial de reentrenamientos."""
        return {
            'total_retrains': self.current_state.get('retrain_count', 0),
            'last_retrain': self.current_state.get('last_retrain'),
            'last_check': self.current_state.get('last_check')
        }

def main():
    """Función principal para uso en GitHub Actions."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor de datos para reentrenamiento')
    parser.add_argument('--threshold', type=int, default=100, help='Número mínimo de nuevas filas para reentrenar')
    parser.add_argument('--data-dir', default='data', help='Directorio de datos')
    parser.add_argument('--action', choices=['check', 'mark-completed', 'history'], default='check', help='Acción a realizar')
    
    args = parser.parse_args()
    
    monitor = DataMonitor(
        data_dir=args.data_dir,
        threshold=args.threshold
    )
    
    if args.action == 'check':
        needs_retrain, info = monitor.check_for_new_data()
        monitor.save_state()
        
        # Para GitHub Actions: establecer output
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"needs_retrain={str(needs_retrain).lower()}\n")
                f.write(f"new_rows={max(info['new_X_rows'], info['new_y_rows'])}\n")
        
        # Exit code para GitHub Actions
        sys.exit(0 if needs_retrain else 1)
        
    elif args.action == 'mark-completed':
        monitor.mark_retrain_completed()
        
    elif args.action == 'history':
        history = monitor.get_retrain_history()
        print("📊 Historial de reentrenamientos:")
        print(f"  Total: {history['total_retrains']}")
        print(f"  Último: {history['last_retrain'] or 'Nunca'}")
        print(f"  Última verificación: {history['last_check'] or 'Nunca'}")

if __name__ == "__main__":
    main()