import json
import os

# --- DICIONÁRIO DE ALIANÇAS E PARCERIAS ---
MAPA_ALIANCAS = {
    # Parceiros SMILES (GOL)
    'ITA Airways': 'Smiles',
    'Ethiopian Airlines': 'Smiles',
    'American Airlines': 'Smiles',
    'Air France': 'Smiles',
    'KLM': 'Smiles',
    'Aerolineas Argentinas': 'Smiles',
    'Copa Airlines': 'Smiles',
    'Air Canada': 'Smiles',
    
    # Parceiros LATAM PASS
    'Qatar Airways': 'Latam Pass',
    'Delta Air Lines': 'Latam Pass',
    'British Airways': 'Latam Pass',
    'Iberia': 'Latam Pass',
    'Lufthansa': 'Latam Pass',
    'Swiss': 'Latam Pass',
    'South African Airways': 'Latam Pass',
    
    # Parceiros TUDOAZUL
    'United Airlines': 'Azul',
    'TAP Air Portugal': 'Azul',
    'Turkish Airlines': 'Azul',
    'Emirates': 'Azul'
}

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
    """Essencial para o CRUD da carteira."""
    if not valor_str: return 0.0
    # Se já for float ou int, retorna direto
    if isinstance(valor_str, (int, float)): return float(valor_str)
    
    limpo = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(limpo)
    except ValueError:
        return 0.0

def identificar_programa_fidelidade(nome_cia):
    if not nome_cia: return None
    
    nome_cia_upper = nome_cia.upper()
    
    # 1. Checagem por "contém" para as grandes brasileiras
    if "AZUL" in nome_cia_upper: return "Azul"
    if "LATAM" in nome_cia_upper: return "Latam Pass"
    if "SMILES" in nome_cia_upper or "GOL" in nome_cia_upper: return "Smiles"
        
    # 2. Busca no mapa de alianças (fazendo o match case-insensitive)
    for chave, programa in MAPA_ALIANCAS.items():
        if chave.upper() in nome_cia_upper:
            return programa
            
    return None