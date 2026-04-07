# parser.py
import re

def formatar_local(voo_perna, tipo="departure"):
    """Padroniza e limpa o nome do aeroporto e IATA."""
    iata = voo_perna.get(f'{tipo}AirportCode', '').upper()
    nome_raw = voo_perna.get(f'{tipo}AirportName', '---')
    
    # Limpeza de siglas duplicadas: "Miami (MIA) (MIA)" -> "Miami (MIA)"
    padrao_duplo = f"({iata}) ({iata})"
    if padrao_duplo in nome_raw:
        nome_raw = nome_raw.replace(padrao_duplo, f"({iata})")
    
    # Garante que o IATA esteja no final se não estiver presente
    if iata and f"({iata})" not in nome_raw:
        return f"{nome_raw} ({iata})"
    return nome_raw

def extrair_data(f):
    """Extrai a data no formato DD/MM/AAAA."""
    if not f: return "---"
    dt = f.get('departureDateTime') or f.get('segments', [{}])[0].get('departureDateTime', {})
    if not dt: return "---"
    return f"{dt.get('day', 0):02d}/{dt.get('month', 0):02d}/{dt.get('year')}"

def extrair_hora_fuso(f):
    """Extrai horário e fuso (Ex: 14:30 (UTC-3))."""
    if not f: return "---"
    dt = f.get('departureDateTime') or f.get('segments', [{}])[0].get('departureDateTime', {})
    if not dt: return "---"
    hora = f"{dt.get('hour', 0):02d}:{dt.get('minute', 0):02d}"
    offset = dt.get('offset')
    fuso = f" (UTC{'+' if offset >= 0 else ''}{offset})" if offset is not None else ""
    return f"{hora}{fuso}"

def extrair_duracao_paradas(f):
    """Retorna a duração formatada e o selo de paradas."""
    if not f: return "---", "Direto"
    mins = f.get('durationMinutes') or 0
    stops = f.get('stopsCount', 0)
    duracao = f"{mins // 60}h {mins % 60}m"
    label = f"{stops} Parada(s)" if stops > 0 else "Direto"
    return duracao, label