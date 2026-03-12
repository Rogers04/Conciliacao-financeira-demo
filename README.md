📊 Automação e Conciliação Financeira (Mercado Pago + Google Sheets)

Este projeto é uma solução de ponta a ponta para automatizar a extração, transformação e visualização de dados financeiros. O objetivo é eliminar o trabalho manual de digitação de extratos e fornecer um painel de controlo (Dashboard) interativo para análise inteligente de gastos e receitas.

Links do Projeto a Funcionar:
- **Web App (Dashboard Interativo):** [https://conciliacao-financeira-demo-cdpwojvbqu7quafsymhqki.streamlit.app]
- **Base de Dados na Nuvem (Google Sheets):** [https://docs.google.com/spreadsheets/d/1CZxKckhbZqAAilTIS03zdO8mhN72lr1XXHxpK_3yzNo/edit?usp=sharing]

O Desafio:
O processo de fechar contas no final do mês consome muito tempo e é suscetível a erros humanos. O desafio era criar um pipeline de dados que extraísse as transações automaticamente de uma conta bancária e as transformasse numa visualização clara e dinâmica em segundos.

Tecnologias Utilizadas (Stack):

* **JavaScript (Google Apps Script):** Responsável por consumir a API do Mercado Pago, extrair o JSON das transações e popular automaticamente a folha de cálculo.
* **Python:** Para a criação do pipeline de dados (ETL - Extração, Transformação e Carga).
* **Streamlit:** Framework utilizado para construir a interface web (Front-end) de forma rápida e responsiva.
* **Plotly:** Biblioteca utilizada para a renderização dos gráficos dinâmicos e interativos.
* **Google Sheets API:** Atua como a nossa base de dados e armazenamento na nuvem.

(Se quiseres clonar este repositório e correr o Dashboard na tua máquina local, segue os passos abaixo):

Como executar este projeto localmente?

1. Clona o repositório:
   ```bash
   git clone [https://github.com/Rogers04/Conciliacao-financeira-demo.git](https://github.com/Rogers04/Conciliacao-financeira-demo.git)

2. Instala as dependências necessárias (certifica-te de que tens o Python instalado):
   ```bash
   pip install streamlit plotly pandas

3. Executa a aplicação do Streamlit:
   ```bash
    streamlit run app.py

  Atenção! 
(Certifique-se de que o nome do teu ficheiro principal python é app.py, caso contrário altera no comando acima)



Desenvolvido por: Rogers Lucas

 - https://github.com/Rogers04
 - [rogers04.github.io/Portfolio-Data/](https://rogers04.github.io/Portfolio-Data/)
