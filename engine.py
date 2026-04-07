import requests
import time
from scraper import obter_token_sessao 

# Configuração de Headers para simular navegador real na API de Poll
HEADERS_AUDITORIA = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Origin': 'https://bestflightsprices.com',
    'Referer': 'https://bestflightsprices.com/',
    'Accept': 'application/json, text/plain, */*'
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

def processar_dados(itinerarios, pax):
    """Processa a lista, filtra as 2 melhores opções por CIA e prepara para o Dashboard."""
    taxas = obter_cotacoes()
    pax_int = max(1, int(pax))
    
    voos_por_cia = {}

    print(f"\n--- 🛰️  FILTRANDO {len(itinerarios)} ITINERÁRIOS (TOP 2 POR CIA) ---")

    for item in itinerarios:
        try:
            if not item.get('bestPrice'): continue
            
            v_ida = item.get('outboundFlight', {})
            v_volta = item.get('inboundFlight', {})
            cia_nome = v_ida.get('carrierName', 'Desconhecida')

            # --- LÓGICA DE MONTAGEM DE ORIGEM/DESTINO (ROBUSTA) ---
            def formatar_local(voo_perna, tipo="departure"):
                iata = voo_perna.get(f'{tipo}AirportCode', '').upper()
                nome_raw = voo_perna.get(f'{tipo}AirportName', '---')
                
                # Se a sigla aparece duplicada (ex: "Miami (MIA) (MIA)"), limpa para apenas uma
                padrao_duplo = f"({iata}) ({iata})"
                if padrao_duplo in nome_raw:
                    nome_raw = nome_raw.replace(padrao_duplo, f"({iata})")
                
                # Se o nome não tem a sigla, adiciona. Se já tem (uma vez), mantém.
                if iata and f"({iata})" not in nome_raw:
                    return f"{nome_raw} ({iata})"
                return nome_raw

            origem_fmt = formatar_local(v_ida, "departure")
            destino_fmt = formatar_local(v_ida, "arrival")

            # 1. Cálculos de Preço e Moeda
            moeda = item.get('currencyCode', 'USD')
            valor_raw = float(item.get('bestPrice', 0))
            if valor_raw > 100000: valor_raw /= 1000 
            
            cotacao = taxas.get(moeda, taxas.get('USD'))
            preco_total_brl = valor_raw * cotacao
            preco_por_pessoa = preco_total_brl / pax_int

            # 2. Funções Auxiliares de Formatação
            def extrair_data(f):
                if not f: return "---"
                dt = f.get('departureDateTime') or f.get('segments', [{}])[0].get('departureDateTime', {})
                if not dt: return "---"
                return f"{dt.get('day', 0):02d}/{dt.get('month', 0):02d}/{dt.get('year')}"

            def extrair_hora_fuso(f):
                if not f: return "---"
                dt = f.get('departureDateTime') or f.get('segments', [{}])[0].get('departureDateTime', {})
                if not dt: return "---"
                hora = f"{dt.get('hour', 0):02d}:{dt.get('minute', 0):02d}"
                offset = dt.get('offset')
                fuso = f" (UTC{'+' if offset >= 0 else ''}{offset})" if offset is not None else ""
                return f"{hora}{fuso}"

            def extrair_duracao_paradas(f):
                if not f: return "---", "Direto"
                mins = f.get('durationMinutes') or 0
                stops = f.get('stopsCount', 0)
                duracao = f"{mins // 60}h {mins % 60}m"
                label = f"{stops} Parada(s)" if stops > 0 else "Direto"
                return duracao, label

            dur_ida, stop_ida = extrair_duracao_paradas(v_ida)
            dur_volta, stop_volta = extrair_duracao_paradas(v_volta)

            # Montagem do objeto de voo
            voo_processado = {
                "valor_sort": preco_por_pessoa,
                "valor_total_reserva": preco_total_brl,
                "pax_count": pax_int,
                "origem": origem_fmt,
                "destino": destino_fmt,
                "tipo": "RT" if (v_volta and v_volta.get('carrierName')) else "OW",
                "cia": cia_nome,
                "ida_data": extrair_data(v_ida),
                "ida_hora": extrair_hora_fuso(v_ida),
                "ida_duracao": dur_ida,
                "ida_paradas": stop_ida,
                "volta_data": extrair_data(v_volta),
                "volta_hora": extrair_hora_fuso(v_volta),
                "volta_duracao": dur_volta,
                "volta_paradas": stop_volta,
                "link": item.get('bookingLink')
            }

            if cia_nome not in voos_por_cia:
                voos_por_cia[cia_nome] = []
            voos_por_cia[cia_nome].append(voo_processado)

        except Exception as e:
            print(f"⚠️ [ENGINE] Erro ao processar item: {e}")
            continue

    # 4. Seleção dos Top 2 de cada CIA e Print de Auditoria
    resultados_finais = []
    for cia, lista_voos in voos_por_cia.items():
        top_da_cia = sorted(lista_voos, key=lambda x: x['valor_sort'])[:2]
        
        for v in top_da_cia:
            print(f"✈️  [AUDITORIA] {v['cia']} | {v['origem']} -> {v['destino']} | R$ {v['valor_sort']:,.2f}")
            resultados_finais.append(v)

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
                    return processar_dados(itins, pax)
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ [ENGINE] Erro no polling: {e}")
            continue
            
    return []