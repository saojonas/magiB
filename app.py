import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MagiB", layout="wide")
st.title("MagiB")
st.subheader("Manutenção de ativos e gerenciamento inteligente")

# --- 2. CARREGAMENTO DE DADOS (Cache para não recarregar toda hora) ---
# Em vez de pd.read_csv...
# --- 2. CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    # 1. Carrega o arquivo para uma variável 'df' (NÃO use return aqui ainda)
    df = pd.read_parquet('dados_frota.parquet')

    # SE O SEU PARQUET JÁ VIER TRATADO DO ETL, VOCÊ PODE PULAR ESTAS DUAS LINHAS DE DATA:
    # (Mas mantive aqui por segurança caso o parquet ainda tenha data numérica)
    if 'data_real' not in df.columns:
        df['data_numerica'] = pd.to_numeric(df['data'], errors='coerce')
        df['data_real'] = pd.to_datetime(df['data_numerica'], unit='D', origin='1899-12-30')
    
    # 2. Filtro de Problemas (Onde Status é 2)
    # Importante: O .copy() evita avisos de "SettingWithCopy"
    df = df[df['status'] == 2].copy()
    
    # 3. Cálculo de Atraso
    hoje = pd.Timestamp.now()
    # Garante que a coluna é datetime antes de subtrair
    df['data_real'] = pd.to_datetime(df['data_real']) 
    df['dias_atraso'] = (hoje - df['data_real']).dt.days
    
    # 4. Tag de Segurança
    termos_seguranca = ['Freio', 'Cinto', 'Pneu', 'Farol', 'Luz', 'Sinalização']
    # A lógica estava certa, só precisava ser executada!
    df['e_seguranca'] = df['item'].apply(lambda x: any(t.lower() in str(x).lower() for t in termos_seguranca))
    
    # AGORA SIM, retornamos o df pronto
    return df

df = carregar_dados()

# --- 3. BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros")
opcao_visualizacao = st.sidebar.radio("Modo de Visão", ["Visão Geral da Frota", "Análise por Veículo"])

# --- 4. CONSTRUÇÃO DO DASHBOARD ---

if opcao_visualizacao == "Visão Geral da Frota":
    # KPIs (Indicadores no topo)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Problemas", len(df))
    col2.metric("Críticos de Segurança", len(df[df['e_seguranca']]))
    col3.metric("Média de Atraso (Dias)", f"{df['dias_atraso'].mean():.1f}")
    
    # Gráficos Lado a Lado
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Top Veículos com Defeitos")
        top_v = df['veiculo'].value_counts().head(5)
        st.bar_chart(top_v)
        
    with c2:
        st.subheader("Defeitos por Sistema")
        st.bar_chart(df['sistema'].value_counts())

    # Tabela de Semáforo
    st.subheader("🚨 Fila de Prioridade (Segurança & Atraso)")
    # Filtrar apenas os críticos para a home
    criticos = df[(df['e_seguranca']) | (df['dias_atraso'] > 15)]
    st.dataframe(criticos[['veiculo', 'item', 'dias_atraso', 'observacao']].sort_values('dias_atraso', ascending=False))

elif opcao_visualizacao == "Análise por Veículo":
    # Selectbox dinâmico
    lista_veiculos = df['veiculo'].unique()
    veiculo_selecionado = st.sidebar.selectbox("Selecione o Veículo", lista_veiculos)
    
    # Filtrar dados
    df_v = df[df['veiculo'] == veiculo_selecionado]
    
    st.header(f"Ficha Técnica: {veiculo_selecionado}")
    
    # KPIs do Veículo
    k1, k2 = st.columns(2)
    k1.metric("Defeitos Pendentes", len(df_v))
    k2.metric("Maior Atraso", f"{df_v['dias_atraso'].max()} dias")
    
    # Tabela detalhada
    st.table(df_v[['data_real', 'sistema', 'item', 'observacao']])