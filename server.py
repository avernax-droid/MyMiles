from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, make_response, session
import json
import os
import csv
import io
from datetime import datetime

# Módulos do Projeto
from engine import buscar_voos_completos
from models import db, User, Carteira, HistoricoBusca
from utils.helpers import carregar_base_sniper, limpar_nome_aeroporto, converter_moeda_para_float

# Importação do Blueprint
from routes.carteira import carteira_bp

# Flask Login
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'TonMix_Secret_99'

# --- CONFIGURAÇÃO MYSQL ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:TonMix%2325@localhost:3307/mymiles_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Registro do Blueprint da Carteira
app.register_blueprint(carteira_bp)

login_manager = LoginManager(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- CARREGAMENTO DE DADOS INICIAIS ---
db_aeroportos = carregar_base_sniper('aeroportos_sniper.json')

# --- ROTAS DE AUTENTICAÇÃO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, senha):
            login_user(user)
            return redirect(url_for('index'))
        flash('E-mail ou senha incorretos.', 'danger')
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email').lower()
        senha = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'warning')
            return redirect(url_for('cadastro'))
        db.session.add(User(nome=nome, email=email, password=generate_password_hash(senha)))
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.pop('filtros_mymiles', None)
    logout_user()
    return redirect(url_for('login'))

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
@login_required
def index():
    filtros = session.get('filtros_mymiles')
    compras = Carteira.query.filter_by(user_id=current_user.id).all()
    if compras:
        investimento_total = sum(float(c.valor_pago) for c in compras)
        saldo_total = sum(c.quantidade for c in compras)
        cpm_real = (investimento_total / (saldo_total / 1000)) if saldo_total > 0 else 17.50
    else:
        cpm_real = 17.50
    return render_template('index.html', user=current_user, filtros=filtros, cpm_padrao=cpm_real)

@app.route('/api/aeroportos')
@login_required
def api_aeroportos():
    query = request.args.get('q', '').lower()
    res = [a for a in db_aeroportos if query in str(a.get('search_key')).lower()]
    return jsonify(res[:10])

@app.route('/buscar', methods=['POST'])
@login_required
def buscar():
    d = request.json
    session['filtros_mymiles'] = d
    res = buscar_voos_completos(d['origem'].upper(), d['destino'].upper(), d['data_ida'], d['data_volta'], float(d['custo_milheiro']), int(d['pax']), d['classe'])
    
    if res and len(res) > 0:
        try:
            melhor_voo = res[0]
            taxa_estimada = 480 if d['data_volta'] else 240
            limite_calculado = int((float(melhor_voo['valor_sort']) - taxa_estimada) / (float(d['custo_milheiro']) / 1000))
            
            origem_final = limpar_nome_aeroporto(d['origem_nome'], d['origem'])
            destino_final = limpar_nome_aeroporto(d['destino_nome'], d['destino'])
            
            novo_historico = HistoricoBusca(
                user_id=current_user.id, origem_iata=d['origem'].upper(), origem_nome=origem_final,
                destino_iata=d['destino'].upper(), destino_nome=destino_final,
                data_ida=datetime.strptime(d['data_ida'], '%Y-%m-%d').date(),
                data_volta=datetime.strptime(d['data_volta'], '%Y-%m-%d').date() if d['data_volta'] else None,
                classe=d['classe'], pax=int(d['pax']), melhor_cia=melhor_voo['cia'],
                melhor_preco_rs=float(melhor_voo['valor_sort']), limite_milhas=limite_calculado,
                valor_milheiro_usado=float(d['custo_milheiro'])
            )
            db.session.add(novo_historico)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar histórico: {e}")
            
    return jsonify({"status": "sucesso", "dados": res})

@app.route('/historico')
@login_required
def historico():
    buscas = HistoricoBusca.query.filter_by(user_id=current_user.id).order_by(HistoricoBusca.data_consulta.desc()).all()
    return render_template('historico.html', user=current_user, buscas=buscas)

@app.route('/historico/exportar')
@login_required
def exportar_historico():
    buscas = HistoricoBusca.query.filter_by(user_id=current_user.id).order_by(HistoricoBusca.data_consulta.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Data Consulta', 'Origem', 'Destino', 'Data Ida', 'Data Volta', 'Cia', 'Preço (R$)', 'Limite Milhas', 'Milheiro Base'])
    for b in buscas:
        origem_csv = limpar_nome_aeroporto(b.origem_nome, b.origem_iata)
        destino_csv = limpar_nome_aeroporto(b.destino_nome, b.destino_iata)
        writer.writerow([
            b.data_consulta.strftime('%d/%m/%Y %H:%M'), 
            origem_csv, 
            destino_csv, 
            b.data_ida.strftime('%d/%m/%Y'), 
            b.data_volta.strftime('%d/%m/%Y') if b.data_volta else '-', 
            b.melhor_cia, 
            f"{float(b.melhor_preco_rs):.2f}".replace('.', ','), 
            b.limite_milhas, 
            f"{float(b.valor_milheiro_usado):.2f}".replace('.', ',')
        ])
    conteudo_csv = "\ufeff" + output.getvalue()
    response = make_response(conteudo_csv)
    filename = f"mymiles_historico_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)