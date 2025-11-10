#!/usr/bin/env python3.11
"""
Script para fazer previsões com o modelo Gradient Boosting treinado.
Recebe um arquivo JSON com oportunidades e retorna as previsões em dias para fechamento.
"""

import json
import sys
import pandas as pd
import numpy as np
import joblib
from data_prep import load_and_prepare_data

# Caminhos dos arquivos do modelo
MODEL_FILE = 'gradient_boosting_model.joblib'
FEATURES_FILE = 'model_features.joblib'

def prepare_prediction_data(opportunities):
    """
    Preparar dados de oportunidades para previsão.
    Similar à função load_and_prepare_data, mas sem calcular a variável alvo.
    """
    # Converter para DataFrame
    df = pd.DataFrame(opportunities)

    # Seleção de Features (mesmas usadas no treinamento)
    features = [
        'ORIGEM',
        'ETAPA ATUAL',
        'ESN',
        'GSN',
        'TIPO DE ATUAÇÃO',
        'PRODUTO DA OPORTUNIDADE',
        'PRODUTO SUGERIDO',
        'VALOR SUGERIDO',
        'VALOR VENDIDO',
    ]

    # Selecionar apenas as colunas disponíveis
    available_features = [f for f in features if f in df.columns]
    df_features = df[available_features].copy()

    # Tratamento de valores ausentes
    df_features['VALOR SUGERIDO'] = df_features['VALOR SUGERIDO'].fillna(0)
    df_features['VALOR VENDIDO'] = df_features['VALOR VENDIDO'].fillna(0)

    # One-Hot Encoding para colunas categóricas
    categorical_cols = df_features.select_dtypes(include=['object']).columns
    df_features = pd.get_dummies(df_features, columns=categorical_cols, drop_first=True)

    return df_features

def predict_opportunities(input_file, output_file):
    """
    Fazer previsões para oportunidades.
    """
    try:
        # Carregar dados de entrada
        with open(input_file, 'r') as f:
            opportunities = json.load(f)

        # Carregar modelo e features
        model = joblib.load(MODEL_FILE)
        feature_names = joblib.load(FEATURES_FILE)

        # Preparar dados
        X_pred = prepare_prediction_data(opportunities)

        # Garantir que X_pred tenha as mesmas colunas que o modelo foi treinado
        # Adicionar colunas faltantes com valor 0
        for col in feature_names:
            if col not in X_pred.columns:
                X_pred[col] = 0

        # Remover colunas extras
        X_pred = X_pred[feature_names]

        # Fazer previsões
        predictions = model.predict(X_pred)

        # Converter para dicionário (índice -> dias para fechamento)
        predictions_dict = {str(i): int(max(0, pred)) for i, pred in enumerate(predictions)}

        # Salvar resultados
        with open(output_file, 'w') as f:
            json.dump(predictions_dict, f)

        print(f"Previsões salvas em {output_file}")
        return True

    except Exception as e:
        print(f"Erro ao fazer previsões: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python predict.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    success = predict_opportunities(input_file, output_file)
    sys.exit(0 if success else 1)
