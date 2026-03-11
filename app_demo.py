import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1 Configuração da página

st.set_page_config(
    page_title="Dashboard Financeir | Portfolio",
    page_icon="",
    layout="wide"
)

st.title("Controle e Conciliação Financeira")
st.markdown("Bem-vindo ao meu sistema financeiro automatizado. Os dados abaixo são gerados via integração " \
"           simulada e processados com Pandas")

# 2. Conexão e Carregamento de Dados
# O TTL (Time to Live) de 600 sedundos (10 min) evita chamdas excessivas à API do google

@st.cache_data(ttl=600)
def carregar_dados():
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Lendo as abas exatas
    df_contas = conn.read(worksheet="CONTAS_A_PAGAR")
    df_vr = conn.read(worksheet="VR")
    df_extrato = conn.read(worksheet="EXTRATO_TRATADO")


    # Convertendo as colunas de Data para o tipo datetime do Pandas para filtrar depois
    df_contas = df_contas.dropna(how="all")
    df_extrato = df_extrato.dropna(how="all")
    df_vr = df_vr.dropna(how="all")

    # Padronizar as datas para o Pandas
    df_contas['Data de Vencimento'] = pd.to_datetime(df_contas["Data de Vencimento"])
    df_extrato['Data'] = pd.to_datetime(df_extrato["Data"])

    return df_contas, df_extrato

try:
    df_contas, df_extrato, df_vr = carregar_dados()

except Exception as e:
    st.error(f"Erro ao carregar dados da planilha. Erro: {e}")
    st.stop

# 3. Processamento de Dados
# Métricas do Extrato Principal

total_entradas = df_extrato[df_extrato['Tipo'] == 'Entrada']['Valor'].sum()
total_saidas = df_extrato[df_extrato['Tipo'] == 'Saída']['Valor'].sum()
saldo_atual = total_entradas - total_saidas
total_pendente = df_contas[df_contas['Status'] == 'Pendente']['Valor'].sum()

# Métricas do VR

vr_entradas = df_vr[df_vr['Tipo'] == 'Entrada']['Valor'].sum() if 'Tipo' in df_vr.columns else 0
vr_saidas = df_vr[df_vr['Tipo'] == 'Saída']['Valor'].sum() if 'Tipo' in df_vr.columens else 0
saldo_vr = vr_entradas - vr_saidas

# 4. Exibição de KPIs 

st.subheader("Resumo Geral das Contas")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total de Entradas", f"R$ {total_entradas:,.2f}")
col2.metric("Total de Saídas", f"R$ {total_saidas:,.2f}", delta="Saídas", delta_color="inverse")
col3.metric("Saldo Bancário", f"R$ {saldo_atual:,.2f}")
col4.metric("Contas Pendentes", f"R$ {total_pendente:,.2f}", delta="Atenção", delta_color="off")

col5.metric("Saldo VR", f"R$ {saldo_vr:,.2f}", delta="Benefício", delta_color="normal")

st.divider()

# 5. Seção de Gráficos 
st.subheader("Fluxo de Caixa (Banco)")
df_grafico = df_extrato.groupby(['Data', 'Tipo'])['Valor'].sum().reset_index()
df_grafico_pivot = df_grafico.pivot(index='Data', columns='Tipo', values= 'Valor').fillna(0)
st.bar_chart(df_grafico_pivot, use_container_width=True)


st.divider()

# 6. Exibição Detalhada (Tabelas) com Abas
st.subheader("Detalhamento de Transaçõaes")

tab1, tab2, tab3 = st.tabs(["Contas a Pagar", "Extrato MP", "Extrato VR"])

with tab1:
    st.dataframe(df_contas, use_container_width=True, hide_index=True)

with tab2:
    st.dataframe(df_extrato, use_container_width=True, hide_index=True)

with tab3:
    # Tabela VR
    st.markdown("### Histórico de Uso do Vale Refeição")
    st.dataframe(df_vr, use_container_width=True, hide_index=True)