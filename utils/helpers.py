import json
import os

def carregar_base_sniper(caminho_json='aeroportos_sniper.json'):
    """Carrega a base de dados de aeroportos."""
    if not os.path.exists(caminho_json): return []
    try:
        with open(caminho_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return []

def limpar_nome_aeroporto(nome, iata):
    """Mesma lógica que usamos no parser, mas para a interface web."""
    if not nome: return "---"
    iata = iata.upper()
    padrao_duplo = f"({iata}) ({iata})"
    if padrao_duplo in nome:
        nome = nome.replace(padrao_duplo, f"({iata})")
    if f"({iata})" in nome:
        return nome
    return f"{nome} ({iata})"

def converter_moeda_para_float(valor_str):
    """Essencial para o CRUD da carteira que você implementou."""
    if not valor_str: return 0.0
    limpo = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(limpo)
    except ValueError:
        return 0.0