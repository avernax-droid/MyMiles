from models import db, HistoricoBusca, Aquisicao
from datetime import datetime

def salvar_aquisicao_milhas(user_id, dados_form):
    try:
        nova = Aquisicao(
            user_id=user_id,
            programa=dados_form.get('programa'),
            quantidade=int(dados_form.get('quantidade')),
            valor_pago=float(dados_form.get('valor_pago')),
            data_operacao=datetime.strptime(dados_form.get('data_compra'), '%Y-%m-%d')
        )
        db.session.add(nova)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar aquisição: {e}")
        return False

def salvar_historico_busca(user_id, dados_busca, melhor_resultado, cpm_usado):
    try:
        dv = dados_busca.get('data_volta')
        data_v = datetime.strptime(dv, '%Y-%m-%d') if dv and dv.strip() else None
        
        nova_busca = HistoricoBusca(
            user_id=user_id,
            origem_iata=dados_busca['origem'].upper(),
            origem_nome=dados_busca.get('origem_nome', ''), 
            destino_iata=dados_busca['destino'].upper(),
            destino_nome=dados_busca.get('destino_nome', ''), 
            data_ida=datetime.strptime(dados_busca['data_ida'], '%Y-%m-%d'),
            data_volta=data_v,
            classe=dados_busca.get('classe'),
            pax=int(dados_busca.get('pax', 1)),
            melhor_cia=melhor_resultado['cia'] if melhor_resultado else "Nenhum",
            melhor_preco_rs=melhor_resultado['valor_total_reserva'] if melhor_resultado else 0,
            valor_milheiro_usado=cpm_usado
        )
        db.session.add(nova_busca)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar histórico: {e}")
        return False