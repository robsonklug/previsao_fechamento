import streamlit as st
import pandas as pd
import joblib
from datetime import date, timedelta
import numpy as np

# --- Configurações Iniciais ---
st.set_page_config(layout="wide", page_title="Previsão de Fechamento de Oportunidades")

# Carregar o modelo e a lista de features
try:
    model = joblib.load('modelo_fechamento.pkl')
    features_list = joblib.load('features_list.pkl')
except FileNotFoundError:
    st.error("Erro: Arquivos do modelo (modelo_fechamento.pkl ou features_list.pkl) não encontrados.")
    st.stop()

# --- Funções de Pré-processamento e Previsão ---

def preprocess_data(df):
    """Padroniza nomes de colunas e filtra oportunidades em aberto."""
    # Padronizar nomes das colunas
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('Á', 'A').str.replace('Ã', 'A').str.replace('Ç', 'C').str.replace('Ê', 'E').str.replace('Õ', 'O').str.replace('Ú', 'U').str.upper()
    
    # Filtrar oportunidades em aberto (DATA_DA_VENDA nula)
    df_abertas = df[df['DATA_DA_VENDA'].isna()].copy()
    
    # Garantir que as colunas de feature existam
    missing_cols = [col for col in features_list if col not in df_abertas.columns]
    if missing_cols:
        st.warning(f"As seguintes colunas de feature estão faltando no arquivo: {', '.join(missing_cols)}. A previsão pode ser imprecisa.")
        # Adicionar colunas faltantes com valor padrão (pode ser necessário um tratamento mais robusto)
        for col in missing_cols:
            df_abertas[col] = np.nan # Adiciona NaN para colunas faltantes
            
    # Garantir que VALOR_SUGERIDO seja numérico
    if 'VALOR_SUGERIDO' in df_abertas.columns:
        df_abertas['VALOR_SUGERIDO'] = pd.to_numeric(df_abertas['VALOR_SUGERIDO'], errors='coerce')
        
    return df_abertas

def predict_closing_days(df_abertas):
    """Faz a previsão dos dias para fechamento e calcula a data provável."""
    if df_abertas.empty:
        return df_abertas

    # 1. Fazer a previsão
    X_predict = df_abertas[features_list]
    
    # O modelo é um Pipeline que inclui o pré-processamento (OneHotEncoder)
    # Ele tratará as novas categorias automaticamente (handle_unknown='ignore')
    predicted_days = model.predict(X_predict)
    
    # Garantir que os dias sejam inteiros e não negativos
    df_abertas['DIAS_PREVISTOS'] = np.maximum(1, np.round(predicted_days)).astype(int)
    
    # 2. Calcular a Data Provável de Fechamento
    data_atual = pd.to_datetime(date.today()) # Convertendo para datetime para consistência
    df_abertas['DATA_PROVAVEL_FECHAMENTO'] = df_abertas['DIAS_PREVISTOS'].apply(lambda x: data_atual + timedelta(days=int(x)))
    
    return df_abertas

# --- Layout do Streamlit ---

st.title("fechamento.app - Previsão de Fechamento de Oportunidades")
st.markdown("Utilize o modelo **Gradient Boosting** treinado com dados históricos para estimar o tempo de fechamento de suas oportunidades em aberto.")

# 1. Upload do arquivo
uploaded_file = st.file_uploader("Selecione a planilha de Oportunidades (formato .xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Carregar o arquivo
        df_raw = pd.read_excel(uploaded_file)
        
        # Pré-processar e filtrar oportunidades em aberto
        df_abertas = preprocess_data(df_raw)
        
        if df_abertas.empty:
            st.success("Não há oportunidades em aberto (com 'DATA_DA_VENDA' vazia) na planilha fornecida.")
        else:
            st.info(f"Foram encontradas **{len(df_abertas)}** oportunidades em aberto para previsão.")
            
            # Fazer a previsão
            df_results = predict_closing_days(df_abertas)
            
            # --- Tarefa 3: Grid de Visualização ---
            st.header("1. Oportunidades com Previsão de Fechamento")
            
            # Selecionar e ordenar colunas
            cols_to_display = [
                'NOME_DA_OPORTUNIDADE', 
                'ETAPA_ATUAL', 
                'VALOR_SUGERIDO', 
                'DIAS_PREVISTOS', 
                'DATA_PROVAVEL_FECHAMENTO',
                'PREVISAO_DE_FECHAMENTO', # Previsão humana original
                'FEELING_FECHAMENTO'     # Feeling humano original
            ]
            
            # Filtrar apenas as colunas que existem no DataFrame
            display_df = df_results[[col for col in cols_to_display if col in df_results.columns]].copy()
            
            # Renomear colunas para melhor visualização
            display_df.rename(columns={
                'NOME_DA_OPORTUNIDADE': 'Oportunidade',
                'ETAPA_ATUAL': 'Etapa',
                'VALOR_SUGERIDO': 'Valor Sugerido',
                'DIAS_PREVISTOS': 'Dias Previstos (IA)',
                'DATA_PROVAVEL_FECHAMENTO': 'Data Provável Fechamento',
                'PREVISAO_DE_FECHAMENTO': 'Previsão Humana',
                'FEELING_FECHAMENTO': 'Feeling Humano (%)'
            }, inplace=True)
            
            # CORREÇÃO: Garantir que a coluna seja do tipo datetime antes de usar .dt
            display_df['Data Provável Fechamento'] = pd.to_datetime(display_df['Data Provável Fechamento'])
            
            # Formatação
            display_df['Valor Sugerido'] = display_df['Valor Sugerido'].map('R$ {:,.2f}'.format)
            display_df['Data Provável Fechamento'] = display_df['Data Provável Fechamento'].dt.strftime('%d/%m/%Y')
            
            # Ordenar pelo campo "Data Provável de Fechamento" (usando a coluna formatada como string, o que é aceitável para o display)
            display_df.sort_values(by='Data Provável Fechamento', inplace=True)
            
            st.dataframe(display_df, use_container_width=True)
            
            # --- Tarefa 4: Gráfico de Projeção de Vendas ---
            st.header("2. Projeção de Vendas (Valor Sugerido) por Mês")
            
            # Criar a coluna de Mês/Ano para o agrupamento
            # Usar a coluna original de data (que é datetime) para o agrupamento
            df_results['MES_ANO_PROVAVEL'] = df_results['DATA_PROVAVEL_FECHAMENTO'].dt.to_period('M')
            
            # Agrupar por Mês/Ano e somar o VALOR_SUGERIDO
            projection_df = df_results.groupby('MES_ANO_PROVAVEL')['VALOR_SUGERIDO'].sum().reset_index()
            projection_df['MES_ANO_PROVAVEL'] = projection_df['MES_ANO_PROVAVEL'].astype(str)
            
            # Filtrar para os próximos 12 meses (a partir do mês atual)
            today = date.today()
            current_month = today.replace(day=1)
            
            # Gerar a lista dos próximos 12 meses
            month_periods = [pd.Period(current_month + timedelta(days=30*i), freq='M') for i in range(12)]
            month_periods_str = [str(p) for p in month_periods]
            
            # Filtrar o DataFrame para os 12 meses de interesse
            projection_df_12m = projection_df[projection_df['MES_ANO_PROVAVEL'].isin(month_periods_str)]
            
            # Garantir que todos os 12 meses estejam presentes (com valor 0 se não houver vendas)
            full_12m_df = pd.DataFrame({'MES_ANO_PROVAVEL': month_periods_str})
            projection_df_12m = pd.merge(full_12m_df, projection_df_12m, on='MES_ANO_PROVAVEL', how='left').fillna(0)
            
            # Criar o gráfico de barras
            import plotly.express as px
            
            fig = px.bar(
                projection_df_12m, 
                x='MES_ANO_PROVAVEL', 
                y='VALOR_SUGERIDO', 
                title='Projeção de Fechamento de Vendas (Valor Sugerido) nos Próximos 12 Meses',
                labels={'MES_ANO_PROVAVEL': 'Mês de Fechamento', 'VALOR_SUGERIDO': 'Valor Total Sugerido (R$)'},
                text_auto='.2s'
            )
            
            fig.update_traces(marker_color='skyblue')
            fig.update_layout(xaxis_tickangle=-45)
            
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
        st.exception(e)

# --- Instruções para o Usuário ---
st.sidebar.header("Instruções")
st.sidebar.markdown("""
1. **Faça o upload** da sua planilha de oportunidades (formato `.xlsx`).
2. A aplicação irá **filtrar** automaticamente as oportunidades que ainda não foram fechadas (onde a coluna `DATA DA VENDA` está vazia).
3. O modelo de **Inteligência Artificial** (Gradient Boosting) fará a previsão dos **Dias Previstos** para o fechamento.
4. A **Data Provável de Fechamento** é calculada como `Data Atual + Dias Previstos`.
5. Os resultados serão exibidos no grid e no gráfico de projeção de vendas.
""")
