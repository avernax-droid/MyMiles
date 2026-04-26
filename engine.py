import requests
import time
import parser 
import get_miles  # IMPORTAÇÃO DO NOVO MÓDULO ESPECIALISTA
from scraper import obter_token_sessao 

# Configuração de Headers para simular navegador real na API de Poll
HEADERS_AUDITORIA = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Origin': 'https://bestflightsprices.com',
    'Referer': 'https://bestflightsprices.com/',
    'Accept': 'application/json, text/plain, */*'
}

# ITEM 2: DICIONÁRIO DE ALIANÇAS
PARCERIAS_AEREAS = {
    'smiles': ['gol', 'american airlines', 'air canada', 'copa', 'aerolineas'],
    'latam': ['qatar', 'delta', 'british', 'iberia', 'lufthansa', 'latam'],
    'azul': ['tap', 'united', 'turkish', 'copa', 'azul'],
    'american': ['american airlines', 'british', 'qatar', 'iberia', 'finnair', 'gol'],
    'lufthansa': ['lufthansa', 'swiss', 'austrian', 'tap', 'united', 'air canada'],
    'qatar': ['qatar', 'american airlines', 'british', 'latam']
}

def obter_cotacoes():
    """Busca cotações em tempo real para converter moedas internacionais."""
    try:
        url = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,GBP-BRL"
        res = requests.get(url, timeout=5).json()
        return {
            'USD': float(res['USDBRL']['bid']), 
            'EUR': float(res['EURBRL']['bid']),
            'GBP': float(res['GBPBRL']['bid']),
            'BRL': 1.0
        }
    except:
        return {'USD': 5.85, 'EUR': 6.30, 'GBP': 7.50, 'BRL': 1.0}

def processar_dados(itinerarios, pax, origem_iata, destino_iata, data_ida):
    """
    Processa a lista, filtra as 2 melhores opções por CIA e audita milhas do Seats.aero.
    """
    taxas = obter_cotacoes()
    pax_int = max(1, int(pax))
    
    # RESTAURADO: Uso do dicionário para filtro de Top 2 por CIA
    voos_por_cia = {}

    print(f"\n--- 🛰️  FILTRANDO {len(itinerarios)} ITINERÁRIOS (TOP 2 POR CIA) ---")

    for item in itinerarios:
        try:
            if not item.get('bestPrice'): continue
            
            v_ida = item.get('outboundFlight', {})
            v_volta = item.get('inboundFlight', {})
            cia_nome = v_ida.get('carrierName', 'Desconhecida')

            # --- CHAMADAS AO MÓDULO PARSER (PRESERVADAS) ---
            origem_fmt = parser.formatar_local(v_ida, "departure")
            destino_fmt = parser.formatar_local(v_ida, "arrival")

            dur_ida, stop_ida = parser.extrair_duracao_paradas(v_ida)
            dur_volta, stop_volta = parser.extrair_duracao_paradas(v_volta)

            # 1. Cálculos de Preço e Moeda
            moeda = item.get('currencyCode', 'USD')
            valor_raw = float(item.get('bestPrice', 0))
            if valor_raw > 100000: valor_raw /= 1000 
            
            cotacao = taxas.get(moeda, taxas.get('USD'))
            preco_total_brl = valor_raw * cotacao
            preco_por_pessoa = preco_total_brl / pax_int

            print(f"✈️  [BESTFLIGHTS] {cia_nome.ljust(15)} | Preço: R$ {preco_por_pessoa:,.2f} | Moeda Orig: {moeda} {valor_raw}")
            
            voo_processado = {
                "valor_sort": preco_por_pessoa,
                "valor_total_reserva": preco_total_brl,
                "pax_count": pax_int,
                "origem": origem_fmt,
                "destino": destino_fmt,
                "tipo": "RT" if (v_volta and v_volta.get('carrierName')) else "OW",
                "cia": cia_nome,
                "ida_data": parser.extrair_data(v_ida),
                "ida_hora": parser.extrair_hora_fuso(v_ida),
                "ida_duracao": dur_ida,
                "ida_paradas": stop_ida,
                "volta_data": parser.extrair_data(v_volta),
                "volta_hora": parser.extrair_hora_fuso(v_volta),
                "volta_duracao": dur_volta,
                "volta_paradas": stop_volta,
                "link": item.get('bookingLink'),
                "milhas_info": None # Campo para o Match
            }

            if cia_nome not in voos_por_cia:
                voos_por_cia[cia_nome] = []
            voos_por_cia[cia_nome].append(voo_processado)

        except Exception as e:
            print(f"⚠️ [ENGINE] Erro ao processar item: {e}")
            continue

    # Seleção dos Top 2 de cada CIA (RESTAURADO)
    resultados_finais = []
    for cia, lista_voos in voos_por_cia.items():
        top_da_cia = sorted(lista_voos, key=lambda x: x['valor_sort'])[:2]
        for v in top_da_cia:
            resultados_finais.append(v)

    # =========================================================================
    # 🧪 TESTE DE CARIMBO (COM INJEÇÃO DE DADOS PARA O DASHBOARD)
    # =========================================================================
    print(f"\n🔍 [AUDITORIA CARIMBO] Consultando Seats.aero ({origem_iata} -> {destino_iata})...")
    dados_milhas = get_miles.get_miles_data(origem_iata, destino_iata, data_ida)

    if dados_milhas:
        print(f"📊 [AUDITORIA CARIMBO] Seats.aero retornou {len(dados_milhas)} opções.")
        for m in dados_milhas:
            nome_prog_seats = m['Airlines'].lower()
            
            for v in resultados_finais:
                nome_cia_best = v['cia'].lower()
                
                match_direto = nome_prog_seats in nome_cia_best or nome_cia_best in nome_prog_seats
                match_parceria = False
                if nome_prog_seats in PARCERIAS_AEREAS:
                    if any(p in nome_cia_best for p in PARCERIAS_AEREAS[nome_prog_seats]):
                        match_parceria = True
                
                if match_direto or match_parceria:
                    # ✅ INJEÇÃO DE DADOS: Agora o HTML vai receber os pontos!
                    v['milhas_info'] = {
                        "pontos": m['EconomyPoints'],
                        "programa": m['Airlines']
                    }
                    print(f"      ✅ MATCH CONFIRMADO: {m['Airlines']} ({m['EconomyPoints']} pts) carimba {v['cia']}")
    else:
        print("⚠️ [AUDITORIA CARIMBO] Nenhum dado de milhas retornado.")
    # =========================================================================

    # Ordenação final para o Front-end
    ordenados = sorted(resultados_finais, key=lambda x: x['valor_sort'])
    
    for r in ordenados:
        r['preco_fmt'] = f"R$ {r['valor_sort']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        r['preco_total_fmt'] = f"R$ {r['valor_total_reserva']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    print(f"✅ PROCESSAMENTO CONCLUÍDO: {len(ordenados)} opções enviadas ao dashboard.\n")
    return ordenados

def buscar_voos_completos(origem, destino, data_ida, data_volta, custo_milheiro, pax, classe):
    """Orquestra a captura do token e a busca dos resultados via API de Poll."""
    token = obter_token_sessao(origem, destino, data_ida, data_volta, classe, pax)
    
    if not token: 
        print("⚠️ [ENGINE] Falha ao obter token de sessão.")
        return []
    
    url_poll = f"https://sky-api-778236310566.us-central1.run.app/search/poll/{token}"
    
    for i in range(15):
        try:
            res = requests.get(url_poll, headers=HEADERS_AUDITORIA, timeout=15)
            if res.status_code == 200:
                itins = res.json()
                if isinstance(itins, dict): 
                    itins = itins.get('itineraries', [])
                if itins: 
                    return processar_dados(itins, pax, origem, destino, data_ida)
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ [ENGINE] Erro no polling: {e}")
            continue
            
    return []