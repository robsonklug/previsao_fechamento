import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import numpy as np

# Definindo o caminho do arquivo
file_path = r"C:\Klug\Python\Projeto_15 - Fechemanto Oportunidade\vendas.xlsx"

# 1. Carregar os dados
try:
    df = pd.read_excel(file_path)
    # Padronizar nomes das colunas
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('Á', 'A').str.replace('Ã', 'A').str.replace('Ç', 'C').str.replace('Ê', 'E').str.replace('Õ', 'O').str.replace('Ú', 'U').str.upper()
except Exception as e:
    print(f"Erro ao carregar o arquivo: {e}")
    exit()

# 2. Preparação dos dados de treinamento (Oportunidades Fechadas)
df_fechadas = df[df['DATA_DA_VENDA'].notna()].copy()
df_fechadas['DATA_DA_VENDA'] = pd.to_datetime(df_fechadas['DATA_DA_VENDA'])
df_fechadas['DATA_CICLO_DE_BUSCA'] = pd.to_datetime(df_fechadas['DATA_CICLO_DE_BUSCA'])
df_fechadas['DIAS_PARA_FECHAMENTO'] = (df_fechadas['DATA_DA_VENDA'] - df_fechadas['DATA_CICLO_DE_BUSCA']).dt.days
df_fechadas = df_fechadas[df_fechadas['DIAS_PARA_FECHAMENTO'] > 0] # Filtrar dias inválidos

# 3. Definição de Features (X) e Target (y)
categorical_features = [
    'ORIGEM', 'ETAPA_ATUAL', 'ESN', 'GSN', 'TIPO_DE_ATUACAO',
    'PRODUTO_DA_OPORTUNIDADE', 'PRODUTO_SUGERIDO'
]
numerical_features = ['VALOR_SUGERIDO']
all_features = categorical_features + numerical_features

X = df_fechadas[all_features]
y = df_fechadas['DIAS_PARA_FECHAMENTO']

# 4. Pré-processamento: One-Hot Encoding para variáveis categóricas
preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
    ],
    remainder='passthrough' # Manter colunas numéricas
)

# 5. Criação do Pipeline: Pré-processamento + Modelo
# O GradientBoostingRegressor é robusto e não exige escalonamento para features numéricas
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42))
])

# 6. Treinamento do modelo (usando todos os dados disponíveis para um modelo final)
# Em um cenário real, faríamos um split para validação, mas para este projeto, treinaremos com tudo.
model.fit(X, y)

# 7. Avaliação (apenas para fins de demonstração no console)
y_pred = model.predict(X)
mae = mean_absolute_error(y, y_pred)
r2 = r2_score(y, y_pred)

print(f"Treinamento concluído.")
print(f"Métricas de avaliação (no conjunto de treinamento):")
print(f"MAE (Erro Absoluto Médio): {mae:.2f} dias")
print(f"R-quadrado: {r2:.2f}")

# 8. Salvar o modelo treinado e a lista de features
joblib.dump(model, 'modelo_fechamento.pkl')
joblib.dump(all_features, 'features_list.pkl')

print("\nModelo e artefatos salvos: 'modelo_fechamento.pkl' e 'features_list.pkl'.")
