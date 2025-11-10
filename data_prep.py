import pandas as pd
import numpy as np
from datetime import datetime

def load_and_prepare_data(file_path):
    """
    Carrega a planilha, calcula a variável alvo (dias para fechamento)
    e prepara os dados para o treinamento do modelo.
    """
    try:
        df = pd.read_excel(file_path, sheet_name='Dados Sintéticos')
    except Exception as e:
        print(f"Erro ao ler o arquivo Excel: {e}")
        return None

    # 1. Filtrar Oportunidades Fechadas (Ganhas) para Treinamento
    # A coluna 'DATA DA VENDA' indica o fechamento. Oportunidades com valor
    # nesta coluna e 'ETAPA ATUAL' = 'Ganho' são as que usaremos para treinar.
    # Oportunidades com 'ETAPA ATUAL' = 'Perda' também são fechadas, mas o foco
    # do usuário é prever o tempo de fechamento para as oportunidades *em aberto*.
    # Vamos focar em 'Ganho' para a regressão do tempo.
    df_closed = df[df['ETAPA ATUAL'] == 'Ganho'].copy()

    # 2. Calcular a Variável Alvo: Dias para Fechamento
    # Dias para Fechamento = DATA DA VENDA - DATA CICLO DE BUSCA
    df_closed['DATA DA VENDA'] = pd.to_datetime(df_closed['DATA DA VENDA'])
    df_closed['DATA CICLO DE BUSCA'] = pd.to_datetime(df_closed['DATA CICLO DE BUSCA'])

    # Calcular a diferença em dias
    df_closed['DIAS_PARA_FECHAMENTO'] = (df_closed['DATA DA VENDA'] - df_closed['DATA CICLO DE BUSCA']).dt.days

    # Remover linhas onde o cálculo falhou (ex: data de venda anterior à data de busca)
    df_closed = df_closed[df_closed['DIAS_PARA_FECHAMENTO'] >= 0].reset_index(drop=True)

    # 3. Seleção de Features (Variáveis Preditivas)
    # Vamos usar colunas categóricas e numéricas que podem influenciar o tempo de fechamento.
    # Excluímos colunas de identificação, texto livre, e as colunas de previsão humana
    # conforme a observação do usuário.
    features = [
        'ORIGEM',
        'ETAPA ATUAL', # Embora seja 'Ganho' para o treinamento, é importante para o modelo
        'ESN',
        'GSN',
        'TIPO DE ATUAÇÃO',
        'PRODUTO DA OPORTUNIDADE',
        'PRODUTO SUGERIDO',
        'VALOR SUGERIDO',
        'VALOR VENDIDO',
        # 'FEELING FECHAMENTO' e 'PREVISÃO DE FECHAMENTO' serão ignoradas
    ]

    df_train = df_closed[features + ['DIAS_PARA_FECHAMENTO']].copy()

    # 4. Feature Engineering e Codificação (One-Hot Encoding)
    # Converter colunas categóricas em variáveis dummy
    categorical_cols = df_train.select_dtypes(include=['object']).columns
    df_train = pd.get_dummies(df_train, columns=categorical_cols, drop_first=True)

    # 5. Tratamento de Valores Ausentes (Simples: preencher com 0 ou média)
    # Para VALOR SUGERIDO e VALOR VENDIDO, preencher NaN com 0
    df_train['VALOR SUGERIDO'] = df_train['VALOR SUGERIDO'].fillna(0)
    df_train['VALOR VENDIDO'] = df_train['VALOR VENDIDO'].fillna(0)

    # Separar X (features) e y (target)
    X = df_train.drop('DIAS_PARA_FECHAMENTO', axis=1)
    y = df_train['DIAS_PARA_FECHAMENTO']

    # Salvar a lista de colunas (features) para uso futuro na previsão
    feature_names = X.columns.tolist()

    print(f"Dados de treinamento prontos. Total de amostras: {len(df_train)}")
    print(f"Total de features: {len(feature_names)}")

    return X, y, feature_names

# Exemplo de uso (apenas para testar a preparação)
# X_train, y_train, features = load_and_prepare_data('/home/ubuntu/upload/vendas.xlsx')
# if X_train is not None:
#     print("\nPrimeiras 5 linhas de X_train:")
#     print(X_train.head())
#     print("\nPrimeiras 5 linhas de y_train:")
#     print(y_train.head())
#     print("\nFeatures (colunas) geradas:")
#     print(features)

# Para a próxima fase, vamos encapsular isso em um script de treinamento.
