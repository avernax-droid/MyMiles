import pandas as pd
import json

def processar_base_airports(caminho_input):
    print(f"--- Iniciando limpeza de {caminho_input} ---")
    
    try:
        # Lendo o CSV
        df = pd.read_csv(caminho_input, low_memory=False)
    except FileNotFoundError:
        print("Erro: Arquivo airports.csv não encontrado.")
        return

    # 1. FILTRAGEM: Apenas aeroportos grandes/médios com código IATA e serviço comercial
    df_filt = df[
        (df['type'].isin(['large_airport', 'medium_airport'])) & 
        (df['iata_code'].notna()) &
        (df['scheduled_service'] == 'yes')
    ].copy()

    # 2. DICIONÁRIO DE TRADUÇÃO (Expandido para melhor busca)
    traducoes = {
        "Turin": "Turim|Turin Torino TRN",
        "Warsaw": "Varsóvia|Warsaw Warszawa WAW",
        "New York": "Nova York|Nova Iorque NYC JFK EWR",
        "London": "Londres|London Heathrow Gatwick LHR",
        "Sao Paulo": "São Paulo|Guarulhos Congonhas GRU CGH",
        "Rio de Janeiro": "Rio de Janeiro|Galeão Santos Dumont GIG SDU",
        "Milan": "Milão|Milano Milan MXP",
        "Munich": "Munique|Munchen Munich MUC",
        "Lisbon": "Lisboa|Lisbon LIS",
        "Rome": "Roma|Rome FCO"
    }

    def formatar_dados(row):
        municipio_csv = str(row['municipality'])
        iata = str(row['iata_code'])
        
        if municipio_csv in traducoes:
            info = traducoes[municipio_csv]
            nome_pt = info.split('|')[0]
            tags = info.split('|')[1]
        else:
            nome_pt = municipio_csv
            tags = municipio_csv

        # Exibição: "São Paulo (GRU)"
        display_name = f"{nome_pt} ({iata})"
        
        # Chave de busca interna: tudo que o usuário pode digitar
        search_key = f"{nome_pt} {tags} {iata} {row['name']} {row['iso_country']}".lower()

        return pd.Series({'code': iata, 'name': display_name, 'search_key': search_key})

    df_final = df_filt.apply(formatar_dados, axis=1)
    df_final['country'] = df_filt['iso_country'].values

    # Salva o arquivo que o Flask/API deve ler
    df_final.to_json('aeroportos_sniper.json', orient='records', force_ascii=False, indent=2)
    
    print(f"--- Limpeza Concluída! ---")
    print(f"Aeroportos processados: {len(df_final)}")

if __name__ == "__main__":
    processar_base_airports('airports.csv')