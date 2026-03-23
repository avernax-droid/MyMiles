import json
import re

def extrair_voos_latam(caminho_arquivo):
    """Lê os dados a partir de um arquivo JSON estruturado."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        voos_processados = []
        
        # Navega na estrutura do JSON da LATAM
        for item in dados.get('content', []):
            summary = item.get('summary', {})
            origem = summary.get('origin', {}).get('iataCode')
            destino = summary.get('destination', {}).get('iataCode')
            voo_numero = summary.get('flightCode')
            
            # Pega o preço da primeira marca (geralmente a mais barata)
            brands = summary.get('brands', [])
            if brands:
                primeira_oferta = brands[0]
                valor_milhas = primeira_oferta.get('price', {}).get('amount')
                taxas = primeira_oferta.get('taxes', {}).get('amount')
                
                voos_processados.append({
                    "voo": voo_numero,
                    "origem": origem,
                    "destino": destino,
                    "milhas": valor_milhas,
                    "taxas": taxas
                })
                
        return voos_processados
    except Exception as e:
        print(f"Erro ao ler JSON: {e}")
        return []

def extrair_voos_texto_bruto(texto_bruto):
    """Lê os dados a partir do texto copiado da tela (Regex)."""
    # Regex para capturar: Horário, Origem, Duração, Chegada, Destino, Milhas e Taxas
    padrao = re.compile(
        r"(\d{1,2}:\d{2})\n([A-Z]{3})\nDuração\n([\d\s\w]+min\.)\n"
        r"(\d{1,2}:\d{2}.*?)\n([A-Z]{3})\n"
        r".*?([\d.]+)\smilhas\n\+\sBRL\s([\d,.]+)", 
        re.DOTALL
    )
    
    matches = padrao.findall(texto_bruto)
    resultados = []
    
    for m in matches:
        resultados.append({
            "saida": m[0],
            "origem": m[1],
            "duracao": m[2].strip(),
            "chegada": m[3].strip(),
            "destino": m[4],
            "milhas": int(m[5].replace('.', '')),
            "taxas": float(m[6].replace(',', '.'))
        })
    return resultados

# Exemplo de uso
if __name__ == "__main__":
    # Para testar o JSON:
    # lista = extrair_voos_latam('dados_latam.json')
    # print(lista)
    pass