import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import joblib
import os
from data_prep import load_and_prepare_data

# Caminho para o arquivo de dados
DATA_FILE = '/home/ubuntu/upload/vendas.xlsx'
MODEL_FILE = 'gradient_boosting_model.joblib'
FEATURES_FILE = 'model_features.joblib'

def train_and_save_model():
    """
    Carrega os dados, treina o modelo Gradient Boosting e salva o modelo e as features.
    """
    print("Iniciando carregamento e preparação dos dados...")
    X, y, feature_names = load_and_prepare_data(DATA_FILE)

    if X is None or y is None:
        print("Falha na preparação dos dados. Abortando treinamento.")
        return

    # Dividir dados em treino e teste (opcional, mas boa prática)
    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"Treinando modelo Gradient Boosting com {len(X)} amostras e {len(feature_names)} features...")
    
    # Inicializar o modelo Gradient Boosting Regressor
    # Parâmetros padrão ou ajustados para um bom ponto de partida
    gbr = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    )

    # Treinar o modelo
    gbr.fit(X, y)

    # Salvar o modelo treinado
    joblib.dump(gbr, MODEL_FILE)
    print(f"Modelo salvo em: {MODEL_FILE}")

    # Salvar a lista de nomes das features (colunas)
    joblib.dump(feature_names, FEATURES_FILE)
    print(f"Features salvas em: {FEATURES_FILE}")

    # Opcional: Avaliação básica (RMSE)
    # from sklearn.metrics import mean_squared_error
    # y_pred = gbr.predict(X_test)
    # rmse = mean_squared_error(y_test, y_pred, squared=False)
    # print(f"RMSE no conjunto de teste: {rmse:.2f} dias")

if __name__ == '__main__':
    # Certificar-se de que o data_prep.py está no PATH para importação
    # Como estamos no mesmo diretório, a importação direta funciona.
    train_and_save_model()
