import streamlit as st
from datetime import date, timedelta
from scraper import capturar_token_sniper
from engine import buscar_voos_api, processar_resultados

st.set_page_config(page_title="MyMiles Sniper", page_icon="✈️", layout="wide")

st.title("🎯 MyMiles Sniper - Passagens em Dinheiro")

# Sidebar
st.sidebar.header("Parâmetros de Busca")
origem = st.sidebar.text_input("Origem (IATA)", value="GRU").upper()
destino = st.sidebar.text_input("Destino (IATA)", value="MIA").upper()

# Datas lado a lado
col1, col2 = st.sidebar.columns(2)
with col1:
    data_ida = st.date_input("Data de Ida", value=date.today() + timedelta(days=7))
with col2:
    data_volta = st.date_input("Data de Volta", value=data_ida + timedelta(days=7))

if st.sidebar.button("EXECUTAR SNIPER 🚀"):
    # Chamada do Scraper com Ida e Volta
    with st.spinner("🕵️ Capturando Token de Ida e Volta..."):
        token_atual = capturar_token_sniper(origem, destino, str(data_ida), str(data_volta))
    
    if token_atual:
        st.success(f"✅ Token capturado: `{token_atual[:10]}...`")
        
        with st.spinner("📊 Consultando API de preços..."):
            dados = buscar_voos_api(token_atual)
            
            if dados:
                resultados = processar_resultados(dados)
                st.write("### 📋 Melhores Preços (Ida e Volta)")
                st.dataframe(resultados, use_container_width=True)
            else:
                st.error("A API não retornou dados para este trecho.")
    else:
        st.error("Falha ao capturar o Token. Tente aumentar o tempo de espera no scraper.py.")