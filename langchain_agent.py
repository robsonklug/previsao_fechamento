import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.agents import AgentType
#from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

# Prompt de sistema customizado
SYSTEM_PROMPT = """
Você é um assistente de vendas especializado em previsão de fechamento de contas. 
Sua principal função é analisar o DataFrame de oportunidades de vendas fornecido e responder perguntas do usuário.
Use o contexto da conversa e os dados fornecidos para responder perguntas.
O DataFrame contém informações detalhadas sobre oportunidades de vendas.
Sempre que possível, use a ferramenta 'pandas_df_agent' para analisar os dados.
Se o usuário perguntar sobre a previsão de fechamento, lembre-o que a previsão é feita na aba principal.
Responda de forma clara e profissional, em português.
"""

def create_agent(df: pd.DataFrame, openai_api_key: str, temperature: float):
    """
    Cria e retorna o agente de conversação LangChain com memória.
    """
    if not openai_api_key:
        return None

    # 1. Configuração do LLM
    llm = ChatOpenAI(
        model="gpt-4.1-mini", # Modelo sugerido para tarefas de raciocínio e custo-benefício
        temperature=temperature,
        openai_api_key=openai_api_key
    )

    # 2. Configuração da Memória
    # Usaremos uma memória de buffer de janela para manter o contexto das últimas 5 interações
    memory = ConversationBufferWindowMemory(
        k=5,
        memory_key="chat_history",
        return_messages=True
    )

    # 3. Criação do Agente Pandas
    # O agente Pandas já vem com a ferramenta de análise de DataFrame
    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        agent_type=AgentType.OPENAI_FUNCTIONS,
        extra_tools=[],
        system_message=SYSTEM_PROMPT,
        memory=memory
    )
    
    return agent

# Função para processar a entrada do usuário
def run_agent(agent, prompt: str):
    """
    Executa o agente com o prompt do usuário.
    """
    try:
        response = agent.invoke({"input": prompt})
        return response["output"]
    except Exception as e:
        return f"Desculpe, ocorreu um erro ao processar sua solicitação: {e}"

if __name__ == '__main__':
    # Exemplo de uso (apenas para teste local do script)
    print("Este script é um módulo e não deve ser executado diretamente.")
