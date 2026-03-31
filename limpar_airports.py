import pandas as pd
import json

def processar_base_airports(caminho_input):
    print(f"--- Iniciando limpeza de {caminho_input} ---")
    
    # 1. Carregar o CSV original
    try:
        df = pd.read_csv(caminho_input, low_memory=False)
    except FileNotFoundError:
        print("Erro: Arquivo airports.csv não encontrado.")
        return

    # 2. FILTRAGEM ESTRATÉGICA
    # Removemos helipontos (como o TSS), aeroportos pequenos e pistas desativadas.
    # Mantemos apenas aeroportos médios e grandes que possuem código IATA e serviço comercial.
    df_filt = df[
        (df['type'].isin(['large_airport', 'medium_airport'])) & 
        (df['iata_code'].notna()) &
        (df['scheduled_service'] == 'yes')
    ].copy()

    # 3. DICIONÁRIO DE TRADUÇÃO EXPANDIDO (Com variações de busca para PT-BR)
    traducoes = {
        # América do Norte
        "New York": "Nova York Nova Iorque NYC", 
        "Miami": "Miami", "Orlando": "Orlando", 
        "Los Angeles": "Los Angeles", "Chicago": "Chicago", "Washington": "Washington",
        "Las Vegas": "Las Vegas", "San Francisco": "São Francisco", "Toronto": "Toronto",
        "Mexico City": "Cidade do México", "Vancouver": "Vancouver",
        
        # Europa
        "London": "Londres London Heathrow Gatwick", 
        "Paris": "Paris Orly Charles de Gaulle", 
        "Rome": "Roma Rome", "Milan": "Milão Milano",
        "Lisbon": "Lisboa Lisbon", "Madrid": "Madri Madrid", "Frankfurt": "Frankfurt", 
        "Amsterdam": "Amsterdã Amsterdam", "Zurich": "Zurique Zurich", "Brussels": "Bruxelas",
        "Vienna": "Viena", "Athens": "Atenas", "Prague": "Praga", "Dublin": "Dublin",
        "Munich": "Munique", "Florence": "Florença", "Venice": "Veneza", "Porto": "Porto",
        
        # América do Sul e Caribe
        "Buenos Aires": "Buenos Aires BUE EZE AEP", 
        "Santiago": "Santiago", "Montevideo": "Montevidéu",
        "Bogota": "Bogotá", "Lima": "Lima", "Cancun": "Cancún", "Punta Cana": "Punta Cana",
        "Asuncion": "Assunção", "La Paz": "La Paz",
        
        # Ásia, África e Oceania
        "Tokyo": "Tóquio Toquio Tokyo Haneda Narita", 
        "Beijing": "Pequim Beijing", "Seoul": "Seul Seoul", "Dubai": "Dubai",
        "Doha": "Doha", "Istanbul": "Istambul Istanbul", "Cairo": "Cairo", "Tel Aviv": "Tel Aviv",
        "Sydney": "Sydney", "Bangkok": "Bangkok", "Shanghai": "Xangai Shanghai"
    }

    def traduzir_municipio(municipio_original):
        m_str = str(municipio_original)
        # Tenta encontrar a tradução. Se o nome original contém a chave (ex: "Tokyo/Narita"), traduz.
        for en, pt in traducoes.items():
            if en.lower() in m_str.lower():
                return pt
        return m_str

    def formatar_nome_exibicao(row):
        cidade_en = str(row['municipality'])
        # Pega a tradução (apenas o primeiro nome para exibição limpa)
        cidade_pt = traduzir_municipio(cidade_en).split(' ')[0]
        # Retorna no formato: Cidade (Código IATA)
        return f"{cidade_pt} ({row['iata_code']})"

    # Criamos a coluna 'display_name' que será o texto principal no seu AutoComplete
    df_filt['display_name'] = df_filt.apply(formatar_nome_exibicao, axis=1)
    
    # Criamos uma coluna de busca robusta (search_key)
    def criar_termos_busca(row):
        cidade_en = str(row['municipality']).lower()
        # Aqui pegamos todos os sinônimos (Tóquio, Toquio, Tokyo, etc.)
        cidade_pt_sinonimos = traduzir_municipio(cidade_en).lower()
        iata = str(row['iata_code']).lower()
        nome_aeroporto = str(row['name']).lower()
        
        # Unificamos tudo em uma string para busca parcial
        return f"{cidade_en} {cidade_pt_sinonimos} {iata} {nome_aeroporto}"

    df_filt['search_terms'] = df_filt.apply(criar_termos_busca, axis=1)

    # 4. SELEÇÃO DE COLUNAS FINAIS
    colunas_finais = {
        'iata_code': 'code',
        'display_name': 'name',
        'search_terms': 'search_key',
        'iso_country': 'country'
    }
    
    df_final = df_filt[colunas_finais.keys()].rename(columns=colunas_finais)

    # 5. Salvar em JSON para o servidor
    df_final.to_json('aeroportos_sniper.json', orient='records', force_ascii=False, indent=2)
    
    print(f"--- Limpeza Concluída! ---")
    print(f"Aeroportos originais: {len(df)}")
    print(f"Aeroportos Comerciais (Sniper): {len(df_final)}")
    print("Arquivo gerado: aeroportos_sniper.json")

if __name__ == "__main__":
    processar_base_airports('airports.csv')