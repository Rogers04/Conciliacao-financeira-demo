import re
import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ------------------------------------------- 1. CONFIGURAÇÃO DA PÁGINA ----------------------------------------- #
st.set_page_config(page_title="Dashboard Financeiro", page_icon="📈", layout="wide")
st.title("Controle e Conciliação Financeira")
st.markdown("---")


# -------------------------------------------- 2. CONEXÃO E FUNÇÕES DE APOIO ------------------------------------ # 
@st.cache_resource
def conectar_gsheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = {
        "type": st.secrets["connections"]["gsheets"]["type"],
        "project_id": st.secrets["connections"]["gsheets"]["project_id"],
        "private_key_id": st.secrets["connections"]["gsheets"]["private_key_id"],
        "private_key": st.secrets["connections"]["gsheets"]["private_key"],
        "client_email": st.secrets["connections"]["gsheets"]["client_email"],
        "client_id": st.secrets["connections"]["gsheets"]["client_id"],
        "auth_uri": st.secrets["connections"]["gsheets"]["auth_uri"],
        "token_uri": st.secrets["connections"]["gsheets"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["connections"]["gsheets"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["connections"]["gsheets"]["client_x509_cert_url"]
    }
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# Converte 'R$ 1.200,50' ou '$-' para float 1200.50
def limpar_valor(valor):
    if isinstance(valor, str):
        valor = valor.replace('R$', '').replace('$', '').replace(' ', '')
        valor = valor.replace('.', '').replace(',', '.')
        if not valor or valor == '-' or valor.strip() == '': 
            return 0.0
    return float(valor) if valor else 0.0


# -------------------------------------- 3. CARREGAMENTO ESTRUTURADO -------------------------------------- #
 
@st.cache_data(ttl=600) # Cache para não esgotar a cota do Google
def carregar_contas():
    try:
        client = conectar_gsheets()
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sh = client.open_by_url(sheet_url)
        worksheet = sh.worksheet("CONTAS_A_PAGAR")
        data = worksheet.get_all_values()
        
        if not data: return pd.DataFrame()

        headers = data[0]
        indices = [i for i, h in enumerate(headers) if h.strip() != ""]
        headers_validos = [headers[i] for i in indices]
        dados_limpos = [[linha[i] for i in indices] for linha in data[1:]]
        
        df = pd.DataFrame(dados_limpos, columns=headers_validos)
        
        if 'Valor' in df.columns:
            df['Valor'] = df['Valor'].apply(limpar_valor)
            df = df[df['Valor'] > 0]
            
        return df
    except Exception as e:
        st.error(f"Erro ao ler CONTAS_A_PAGAR: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def carregar_extrato():
#   Função adicionada para fechar tríade do projeto
    try:
        client = conectar_gsheets()
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sh = client.open_by_url(sheet_url)
        worksheet = sh.worksheet("EXTRATO_TRATADO")
        data = worksheet.get_all_values()
        
        if not data: return pd.DataFrame()

        headers = data[0]
        indices = [i for i, h in enumerate(headers) if h.strip() != ""]
        headers_validos = [headers[i] for i in indices]
        dados_limpos = [[linha[i] for i in indices] for linha in data[1:]]
        
        df = pd.DataFrame(dados_limpos, columns=headers_validos)
        
        if 'Valor' in df.columns:
            df['Valor'] = df['Valor'].apply(limpar_valor)
            
        # Extraindo o Mês e Ano da coluna de Data para o filtro global funcionar
        if 'Data' in df.columns:
            df['Data_Datetime'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df['Mês'] = df['Data_Datetime'].dt.strftime('%B').str.capitalize()

        # Traduzindo meses do inglês para português caso o Pandas esteja em EN
            mapa_meses = {'January':'janeiro', 'February':'fevereiro', 'March':'março', 'April':'abril', 'May':'maio', 'June':'junho', 'July':'julho', 'August':'agosto', 'September':'setembro', 'October':'outubro', 'November':'novembro', 'December':'dezembro'}
            df['Mês'] = df['Mês'].replace(mapa_meses)
            df['Ano'] = df['Data_Datetime'].dt.year.astype(str)
            
        return df
    except Exception as e:
        st.error(f"Erro ao ler EXTRATO_TRATADO: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def carregar_vr():
    try:
        client = conectar_gsheets()
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sh = client.open_by_url(sheet_url)
        worksheet = sh.worksheet("VR") 
        data = worksheet.get_all_values()
        
        if not data: return pd.DataFrame()

        titulo = str(data[0]).join(" ") 
        match_ano = re.search(r'202\d', str(data[0])) 
        ano_detectado = match_ano.group(0) if match_ano else "2026" 

        header_index = -1
        headers = []
        
        for i, row in enumerate(data[:10]):
            row_str = [str(c).strip() for c in row] 
            if "janeiro" in row_str:
                header_index = i
                headers = row_str
                break
        
        if header_index == -1: return pd.DataFrame()

        meses_validos = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
        mapa_colunas = {h: i for i, h in enumerate(headers) if h in meses_validos}
        registros = []
        
        for linha in data[header_index + 1:]:
            primeira_celula = str(linha[0]).lower()
            if "total" in primeira_celula or "totais" in primeira_celula: continue
                
            for mes, col_idx in mapa_colunas.items():
                if col_idx < len(linha):
                    valor_bruto = linha[col_idx]
                    valor_limpo = limpar_valor(valor_bruto)
                    
                    if valor_limpo > 0:
                        registros.append({
                            "Mês": mes, "Ano": ano_detectado, "Valor": valor_limpo,
                            "Categoria": "Refeição", "Descrição": "Gasto VR", "Status": "Pago" 
                        })
        
        return pd.DataFrame(registros)
    except Exception as e:
        st.error(f"Erro técnico ao ler aba VR: {e}")
        return pd.DataFrame()

#   CARREGAMENTO GERAL
with st.spinner("Carregando bases de dados..."):
    df_contas = carregar_contas()
    df_extrato = carregar_extrato()
    df_vr = carregar_vr()

#   FILTROS GLOBAIS 
st.sidebar.header("Filtros")

anos_unicos = sorted(list(set(df_contas.get('Ano', [])).union(set(df_vr.get('Ano', []))).union(set(df_extrato.get('Ano', [])))), reverse=True)
if not anos_unicos:
    st.warning("Nenhum dado encontrado.")
    st.stop()

ano_sel = str(st.sidebar.selectbox("Ano", anos_unicos))

ordem_meses = {'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12}

meses_contas = df_contas[df_contas['Ano'].astype(str) == ano_sel]['Mês'].unique() if 'Mês' in df_contas.columns else []
meses_vr = df_vr[df_vr['Ano'].astype(str) == ano_sel]['Mês'].unique() if 'Mês' in df_vr.columns else []
meses_extrato = df_extrato[df_extrato['Ano'].astype(str) == ano_sel]['Mês'].unique() if 'Mês' in df_extrato.columns else []

meses_unicos = list(set(list(meses_contas) + list(meses_vr) + list(meses_extrato)))
meses_unicos.sort(key=lambda x: ordem_meses.get(x, 99))

mes_sel = st.sidebar.selectbox("Mês", meses_unicos)


# ------------------------------------------- INTERFACE DE ABAS -------------------------------------------- #

tab1, tab2, tab3 = st.tabs(["Contas a Pagar", " Extrato Mercado Pago", " Vale Refeição"])


# ------------------------------------------------- ABA 1: CONTAS ------------------------------------------ # 
with tab1:
    st.subheader(f"Gestão de Contas - {mes_sel}/{ano_sel}")
    if not df_contas.empty:
        df_c_filtrado = df_contas[(df_contas['Ano'].astype(str) == ano_sel) & (df_contas['Mês'] == mes_sel)]
        
        if not df_c_filtrado.empty:
            total = df_c_filtrado['Valor'].sum()
            pago = df_c_filtrado[df_c_filtrado['Status'].astype(str).str.lower() == 'pago']['Valor'].sum() if 'Status' in df_c_filtrado.columns else 0
            pendente = df_c_filtrado[df_c_filtrado['Status'].astype(str).str.lower() == 'pendente']['Valor'].sum() if 'Status' in df_c_filtrado.columns else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Total de Contas", f"R$ {total:,.2f}")
            c2.metric("Total Pago", f"R$ {pago:,.2f}")
            c3.metric("Falta Pagar", f"R$ {pendente:,.2f}", delta="-Pendente", delta_color="inverse")
            
            st.divider()
            
            g1, g2 = st.columns(2)
            with g1:
                if 'Categoria' in df_c_filtrado.columns:
                    fig = px.pie(df_c_filtrado, values='Valor', names='Categoria', hole=0.4, title="Despesas por Categoria")
                    st.plotly_chart(fig, use_container_width=True)
            with g2:
                if 'Status' in df_c_filtrado.columns:
                    fig2 = px.bar(df_c_filtrado, x='Status', y='Valor', color='Status', title="Status de Pagamento")
                    st.plotly_chart(fig2, use_container_width=True)
            
            def estilo_status(val):
                if isinstance(val, str):
                    if 'pago' in val.lower(): return 'background-color: #c6efce; color: #006100'
                    if 'pendente' in val.lower(): return 'background-color: #ffeb9c; color: #9c5700'
                return ''
            
            cols_ver = [c for c in ['Data de Vencimento', 'Descrição', 'Categoria', 'Valor', 'Status'] if c in df_c_filtrado.columns]
            st.dataframe(df_c_filtrado[cols_ver].style.map(estilo_status, subset=['Status'] if 'Status' in df_c_filtrado.columns else None), use_container_width=True, hide_index=True)
        else:
            st.info("Sem contas para este período.")

# -------------------------------------------------- ABA 2: EXTRATO -------------------------------------- #
with tab2:
    st.subheader(f"Movimentação Bancária (MP) - {mes_sel}/{ano_sel}")
    if not df_extrato.empty:
        df_e_filtrado = df_extrato[(df_extrato['Ano'].astype(str) == ano_sel) & (df_extrato['Mês'] == mes_sel)]
        
        if not df_e_filtrado.empty:
            entradas = df_e_filtrado[df_e_filtrado['Tipo'].astype(str).str.lower() == 'entrada']['Valor'].sum() if 'Tipo' in df_e_filtrado.columns else 0
            saidas = df_e_filtrado[df_e_filtrado['Tipo'].astype(str).str.lower() == 'saída']['Valor'].sum() if 'Tipo' in df_e_filtrado.columns else 0
            saldo = entradas - saidas

            m1, m2, m3 = st.columns(3)
            m1.metric("Entradas", f"R$ {entradas:,.2f}")
            m2.metric("Saídas", f"R$ {saidas:,.2f}", delta="-Gasto", delta_color="inverse")
            m3.metric("Saldo do Mês", f"R$ {saldo:,.2f}")
            
            st.divider()
            
            # Gráfico de Fluxo Diário usando Plotly 
            if 'Data_Datetime' in df_e_filtrado.columns and 'Tipo' in df_e_filtrado.columns:
                fig_fluxo = px.bar(df_e_filtrado, x='Data_Datetime', y='Valor', color='Tipo', title="Fluxo de Caixa Diário", barmode='group')
                st.plotly_chart(fig_fluxo, use_container_width=True)
            
            st.dataframe(df_e_filtrado.drop(columns=['Data_Datetime', 'Mês', 'Ano'], errors='ignore'), use_container_width=True, hide_index=True)
        else:
            st.info("Sem movimentações no extrato neste período.")
    else:
        st.warning("Extrato não carregado.")

# ----------------------------------------------------- ABA 3: VR --------------------------------------------- # 
with tab3:
    st.subheader(f"Gastos VR - {mes_sel}/{ano_sel}")
    if not df_vr.empty:
        df_vr_filtrado = df_vr[(df_vr['Ano'].astype(str) == ano_sel) & (df_vr['Mês'] == mes_sel)]
        
        if not df_vr_filtrado.empty:
            total_vr = df_vr_filtrado['Valor'].sum()
            qtd_compras = len(df_vr_filtrado)
            media_vr = total_vr / qtd_compras if qtd_compras > 0 else 0
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Total Gasto", f"R$ {total_vr:,.2f}")
            k2.metric("Qtd. Refeições", f"{qtd_compras}")
            k3.metric("Ticket Médio", f"R$ {media_vr:,.2f}")
            
            st.divider()
            
            df_vr_filtrado = df_vr_filtrado.reset_index()
            fig_vr = px.bar(df_vr_filtrado, y='Valor', title="Sequência de Gastos no Mês", labels={'index': 'Ordem da Compra'})
            st.plotly_chart(fig_vr, use_container_width=True)
            
            with st.expander("Ver Extrato Detalhado do VR"):
                st.dataframe(df_vr_filtrado[['Mês', 'Valor', 'Categoria']], use_container_width=True, hide_index=True)
        else:
            st.info(f"Sem gastos lançados no VR em {mes_sel}.")
