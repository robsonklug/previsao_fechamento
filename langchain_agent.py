import pandas as pd

from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from langchain_core.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.prompts.chat import ChatPromptTemplate
#from langchain.memory.buffer_window import ConversationBufferWindowMemory
#from langchain_community.memory import ConversationBufferWindowMemory
#from langchain.agents import initialize_agent
#from langchain.agents import create_react_agent
from langchain_openai import ChatOpenAI


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

    if not isinstance(df, pd.DataFrame):
        raise TypeError("O parâmetro 'df' deve ser um pandas.DataFrame.")
    
    # 1. Configuração do LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini", # Modelo sugerido para tarefas de raciocínio e custo-benefício
        temperature=temperature,
        openai_api_key=openai_api_key
    )

#    # 2. Configuração da Memória
#    # Usaremos uma memória de buffer de janela para manter o contexto das últimas 5 interações
#    memory = ConversationBufferWindowMemory(
#        k=5,
#        memory_key="chat_history",
#        return_messages=True
#    )

    # 3. Criação do Agente Pandas
    # O agente Pandas já vem com a ferramenta de análise de DataFrame
    agent = create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        verbose=True,
        allow_dangerous_code=True,
        agent_type="openai-tools",  # Mais eficiente
        max_iterations=15,  # Limite de iterações
        max_execution_time=60,  # Timeout em segundos
        handle_parsing_errors=True,  # Trata erros gracefully
        system_message=SYSTEM_PROMPT
    )
    
    return agent

# Função para processar a entrada do usuário

def run_agent(agent, prompt: str, timeout: int = 60):
    """
    Executa o agente com o prompt do usuário com timeout.
    """
    try:
        response = agent.invoke(
            {"input": prompt},
            config={"max_execution_time": timeout}
        )
        return response.get("output", "Desculpa, não consegui gerar uma resposta.")
    except TimeoutError:
        return "A análise demorou muito tempo. Tente uma pergunta mais específica."
    except Exception as e:
        return f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"

#def run_agent(agent, prompt: str):
#    """
#    Executa o agente com o prompt do usuário.
#    """
#    try:
#        response = agent.invoke({"input": prompt})
#        return response["output"]
#    except Exception as e:
#        return f"Desculpe, ocorreu um erro ao processar sua solicitação: {e}"

if __name__ == '__main__':
    # Exemplo de uso (apenas para teste local do script)
    print("Este script é um módulo e não deve ser executado diretamente.")
