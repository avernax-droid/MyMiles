import json

def extrair_voos_latam(caminho_arquivo):
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    voos_processados = []
    
    # Navega na estrutura que você acabou de encontrar
    for item in dados.get('content', []):
        summary = item.get('summary', {})
        origem = summary.get('origin', {}).get('iataCode')
        destino = summary.get('destination', {}).get('iataCode')
        voo_numero = summary.get('flightCode')
        
        # Pega o preço da primeira marca (geralmente a LIGHT/mais barata)
        if summary.get('brands'):
            primeira_oferta = summary['brands'][0]
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

# Teste rápido
# lista = extrair_voos_latam('dados_latam.json')
# print(lista)
