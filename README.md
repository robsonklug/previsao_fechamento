# fechamento.app - Previsão de Fechamento de Oportunidades

Este projeto implementa uma aplicação web interativa usando **Streamlit** para prever o tempo de fechamento de oportunidades de vendas, utilizando um modelo de **Machine Learning** (Gradient Boosting).

## Funcionalidades

1.  **Treinamento do Modelo:** O modelo é treinado com dados históricos (oportunidades fechadas) para aprender a relação entre as características da oportunidade e o tempo de fechamento (em dias).
2.  **Previsão:** Permite o upload de uma nova planilha de oportunidades em aberto para prever os dias até o fechamento.
3.  **Data Provável de Fechamento:** Calcula a data provável de fechamento com base na data atual e nos dias previstos pelo modelo.
4.  **Visualização em Grid:** Exibe as oportunidades em aberto, ordenadas pela data provável de fechamento.
5.  **Projeção de Vendas:** Gera um gráfico de barras com a projeção do valor total sugerido das vendas por mês para os próximos 12 meses.

## Estrutura do Projeto

-   `fechamento_app.py`: O código principal da aplicação Streamlit.
-   `model_trainer.py`: Script utilizado para treinar o modelo inicial e gerar os artefatos.
-   `modelo_fechamento.pkl`: O modelo de Gradient Boosting treinado.
-   `features_list.pkl`: Lista das features utilizadas no treinamento do modelo.
-   `requirements.txt`: Lista de dependências para o deploy no Streamlit.io.

## Como Testar Localmente

Para testar a aplicação no seu Visual Studio Code, siga os passos abaixo:

1.  **Pré-requisitos:** Certifique-se de ter o Python (versão 3.8+) instalado.
2.  **Instalar Dependências:** Abra o terminal na pasta do projeto e execute:
    \`\`\`bash
    pip install -r requirements.txt
    \`\`\`
3.  **Preparar os Arquivos:**
    -   Coloque os arquivos `fechamento_app.py`, `modelo_fechamento.pkl`, `features_list.pkl`, `requirements.txt` e `README.md` na mesma pasta.
    -   Você precisará da planilha original `vendas(1).xlsx` para fazer o upload na aplicação.
4.  **Executar a Aplicação:** No terminal, execute o comando:
    \`\`\`bash
    streamlit run fechamento_app.py
    \`\`\`
5.  **Acessar:** O Streamlit abrirá automaticamente a aplicação no seu navegador (geralmente em `http://localhost:8501`).
6.  **Uso:** Faça o upload da planilha `vendas(1).xlsx` (ou uma nova planilha com o mesmo formato) para ver as previsões.

## Notas sobre o Modelo

-   O modelo utiliza o algoritmo **Gradient Boosting Regressor** da biblioteca `scikit-learn`.
-   As colunas categóricas são tratadas com **One-Hot Encoding** dentro de um `Pipeline` para garantir que o pré-processamento seja consistente durante o treinamento e a previsão.
-   A variável alvo é o número de dias entre a `DATA CICLO DE BUSCA` e a `DATA DA VENDA`.
