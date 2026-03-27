import requests
from scraper import obter_token_sessao
import time

def converter_para_real(valor_bruto, moeda):
    """Converte valores internacionais para BRL (Cotações Março/2026)."""
    taxas = {'USD': 5.25, 'GBP': 6.60, 'EUR': 5.70, 'BRL': 1.00}
    return valor_bruto * taxas.get(moeda.upper(), 1.00)

def calcular_score_arbitragem(preco_total_brl, custo_milheiro_user):
    """Calcula se vale a pena usar milhas (estimando R$ 410 de taxas fixas)."""
    # Descontamos uma estimativa de taxa para o cálculo do teto de milhas ser realista
    valor_passagem_pura = preco_total_brl - 410
    if valor_passagem_pura <= 0: return "ANALISAR", "text-muted"

    limite_milhas = int(valor_passagem_pura / (custo_milheiro_user / 1000))
    if limite_milhas > 100000: return "🔥 OPORTUNIDADE", "text-danger fw-bold"
    elif limite_milhas > 50000: return "✅ JUSTO", "text-success fw-bold"
    return "⚠️ CILADA", "text-warning"

def processar_resultados(itinerarios, custo_milheiro_user=17.50):
    voos_formatados = []
    # Ordena pelo menor preço bruto
    itins_ordenados = sorted(itinerarios, key=lambda x: x.get('bestPrice', 999999999))
    
    for item in itins_ordenados:
        try:
            out = item.get('outboundFlight') or {}
            inb = item.get('inboundFlight') or {}
            link = item.get('bookingLink', '#')
            moeda = item.get('currencyCode', 'USD')
            
            # Conversão e formatação monetária
            total_brl = converter_para_real(float(item.get('bestPrice', 0)) / 1000, moeda)
            preco_str = f"R$ {total_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            status, cor = calcular_score_arbitragem(total_brl, custo_milheiro_user)

            def limpar_trecho(flight, sentido, preco_info, is_ida=False):
                dt = flight.get('departureDateTime', {})
                # Captura de data e hora formatada
                data_voo = f"{dt.get('day', 0):02d}/{dt.get('month', 0):02d}/{dt.get('year', 0)}"
                horario = f"{dt.get('hour', 0):02d}:{dt.get('minute', 0):02d}"
                
                duracao_min = flight.get('durationMinutes', 0)
                txt_duracao = f"{duracao_min // 60}h {duracao_min % 60}m"
                paradas = flight.get('stopsCount', 0)

                dados = {
                    "sentido": sentido,
                    "data": data_voo,
                    "voo": flight.get('carrierName', '---'),
                    "trecho": f"{flight.get('departureAirport', '---')} ➔ {flight.get('arrivalAirport', '---')}",
                    "horario": horario,
                    "duracao": txt_duracao,
                    "escalas": "DIRETO" if paradas == 0 else f"{paradas} escala(s)",
                    "preco": preco_info,
                    "link": link
                }
                if is_ida:
                    dados["status_sniper"] = status
                    dados["classe_cor"] = cor
                return dados

            if out:
                voos_formatados.append(limpar_trecho(out, "IDA", preco_str, is_ida=True))
            if inb and inb.get('departureAirport'):
                voos_formatados.append(limpar_trecho(inb, "VOLTA", "---"))

        except Exception as e:
            print(f"⚠️ Erro no processamento: {e}"); continue
    return voos_formatados

def buscar_voos_completos(origem, destino, data_ida, data_volta=None, custo_milheiro=17.50):
    token = obter_token_sessao(origem, destino, data_ida, data_volta)
    if not token: return []
    url = f"https://sky-api-778236310566.us-central1.run.app/search/poll/{token}"
    for i in range(15):
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        if res.status_code == 200:
            dados = res.json()
            itins = dados.get('itineraries', []) if isinstance(dados, dict) else dados
            if itins: return processar_resultados(itins, custo_milheiro)
        time.sleep(4)
    return []