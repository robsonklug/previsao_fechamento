import streamlit as st
import pandas as pd
import joblib
from datetime import date, timedelta
import numpy as np
import plotly.express as px
from langchain_agent import create_agent, run_agent # Importando as funções do agente

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
        # st.warning(f"As seguintes colunas de feature estão faltando no arquivo: {', '.join(missing_cols)}. A previsão pode ser imprecisa.")
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

# Criação das abas
tab_previsao, tab_chat = st.tabs(["Previsão e Projeção", "Chat com a Planilha"])

# --- Aba de Previsão e Projeção ---
with tab_previsao:
    # 1. Upload do arquivo
    uploaded_file = st.file_uploader("Selecione a planilha de Oportunidades (formato .xlsx)", type=["xlsx"], key="upload_previsao")

    if uploaded_file is not None:
        try:
            # Carregar o arquivo
            df_raw = pd.read_excel(uploaded_file)
            
            # Salvar o DataFrame completo na sessão para uso no chat
            st.session_state['df_completo'] = df_raw.copy()
            
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
                
                # Ordenar pelo campo "Data Provável de Fechamento"
                display_df.sort_values(by='Data Provável Fechamento', inplace=True)
                
                st.dataframe(display_df, use_container_width=True)
                
                # --- Tarefa 4: Gráfico de Projeção de Vendas ---
                st.header("2. Projeção de Vendas (Valor Sugerido) por Mês")
                
                # Criar a coluna de Mês/Ano para o agrupamento
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

# --- Aba de Chat com a Planilha ---
with tab_chat:
    st.header("Chat com a Planilha de Oportunidades")
    st.markdown("Faça perguntas sobre os dados da planilha que você carregou na aba 'Previsão e Projeção'.")

    # --- Configuração do LLM (Sidebar) ---
    with st.sidebar:
        st.header("Configuração do Agente LLM")
        
        # Chave OpenAI
        openai_api_key = st.text_input(
            "Chave da API OpenAI", 
            type="password", 
            help="Sua chave da API OpenAI para o agente de conversação."
        )
        
        # Temperatura
        temperature = st.slider(
            "Temperatura do LLM", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.0, 
            step=0.1,
            help="Controla a aleatoriedade das respostas. 0.0 é mais determinístico."
        )
        
        # Botão para limpar o histórico
        if st.button("Limpar Histórico do Chat"):
            st.session_state.messages = []
            st.experimental_rerun()

    # --- Lógica do Chat ---
    
    # Inicializa o histórico de mensagens
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Verifica se o DataFrame foi carregado
    if 'df_completo' not in st.session_state:
        st.warning("Por favor, carregue uma planilha na aba 'Previsão e Projeção' para iniciar o chat.")
    elif not openai_api_key:
        st.warning("Por favor, insira sua Chave da API OpenAI na barra lateral para iniciar o chat.")
    else:
        # Cria o agente (ou recria se as configurações mudaram)
        df_chat = st.session_state['df_completo']
        #agent = create_agent(df_chat, openai_api_key, temperature)
        agent = create_agent(df_raw, openai_api_key, temperature)

        # Exibe mensagens anteriores
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Processa a entrada do usuário
        if prompt := st.chat_input("Pergunte sobre as oportunidades..."):
            # Adiciona a mensagem do usuário ao histórico
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Obtém a resposta do agente
            with st.chat_message("assistant"):
                with st.spinner("Analisando os dados..."):
                    response = run_agent(agent, prompt)
                    st.markdown(response)
            
            # Adiciona a resposta do assistente ao histórico
            st.session_state.messages.append({"role": "assistant", "content": response})

# --- Instruções para o Usuário (Sidebar) ---
with st.sidebar:
    st.header("Instruções da Aplicação")
    st.markdown("""
    **Aba 'Previsão e Projeção':**
    1. Faça o **upload** da sua planilha de oportunidades (`.xlsx`).
    2. O modelo de **IA** fará a previsão dos dias para fechamento.
    3. Visualize o grid de oportunidades e o gráfico de projeção de vendas.
    
    **Aba 'Chat com a Planilha':**
    1. Insira sua **Chave da API OpenAI** e defina a **Temperatura** na barra lateral.
    2. Faça perguntas sobre os dados da planilha carregada.
    """)
