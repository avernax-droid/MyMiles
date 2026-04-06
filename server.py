from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, make_response, session
import json
import os
import csv
import io
from datetime import datetime
from engine import buscar_voos_completos

# Importações para Banco de Dados e Login
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'TonMix_Secret_99'

# --- CONFIGURAÇÃO MYSQL ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:TonMix%2325@localhost:3307/mymiles_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' 

# --- MODELOS DE DADOS ---
class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Aquisicao(db.Model):
    __tablename__ = 'aquisicoes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    programa = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_pago = db.Column(db.Numeric(10, 2), nullable=False)
    data_operacao = db.Column(db.DateTime, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- CARREGAMENTO SNIPER ---
ARQUIVO_JSON = 'aeroportos_sniper.json'
def carregar_base_sniper():
    if not os.path.exists(ARQUIVO_JSON): return []
    try:
        with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return []

db_aeroportos = carregar_base_sniper()

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
    session.pop('filtros_mymiles', None) # Limpa busca ao sair
    logout_user()
    return redirect(url_for('login'))

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
@login_required
def index():
    # Recupera os filtros da sessão para devolver ao formulário
    filtros = session.get('filtros_mymiles')
    return render_template('index.html', user=current_user, filtros=filtros)

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
    
    # SALVAR NA SESSÃO: Salvamos o dicionário completo enviado pelo JS
    # d contém: origem (IATA), origem_nome, destino (IATA), destino_nome, datas, etc.
    session['filtros_mymiles'] = d
    
    res = buscar_voos_completos(
        d['origem'].upper(), 
        d['destino'].upper(), 
        d['data_ida'], 
        d['data_volta'], 
        float(d['custo_milheiro']), 
        int(d['pax']), 
        d['classe']
    )
    return jsonify({"status": "sucesso", "dados": res})

# --- ROTA DA CARTEIRA ---
@app.route('/carteira', methods=['GET', 'POST'])
@login_required
def carteira():
    if request.method == 'POST':
        try:
            nova = Aquisicao(
                user_id=current_user.id,
                programa=request.form.get('programa'),
                quantidade=int(request.form.get('quantidade')),
                valor_pago=float(request.form.get('valor_pago')),
                data_operacao=datetime.strptime(request.form.get('data_compra'), '%Y-%m-%d')
            )
            db.session.add(nova)
            db.session.commit()
            flash("Lançamento salvo!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {e}", "danger")
        return redirect(url_for('carteira'))

    compras = Aquisicao.query.filter_by(user_id=current_user.id).all()
    investimento_total = 0.0
    saldo_total = 0
    milhas_processadas = []

    for c in compras:
        v_pago = float(c.valor_pago)
        investimento_total += v_pago
        saldo_total += c.quantidade
        cpm = (v_pago / (c.quantidade / 1000)) if c.quantidade > 0 else 0
        milhas_processadas.append({
            'data': c.data_operacao.strftime('%d/%m/%Y'),
            'programa': c.programa,
            'quantidade': c.quantidade,
            'valor_pago': v_pago,
            'cpm': cpm
        })

    cpm_geral = (investimento_total / (saldo_total / 1000)) if saldo_total > 0 else 0
    return render_template('carteira.html', user=current_user, milhas=milhas_processadas, investimento=investimento_total, saldo=saldo_total, cpm_geral=cpm_geral)

@app.route('/carteira/exportar')
@login_required
def exportar_carteira():
    compras = Aquisicao.query.filter_by(user_id=current_user.id).order_by(Aquisicao.data_operacao.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Data', 'Programa', 'Quantidade', 'Valor Pago (R$)', 'CPM (R$)'])
    
    for c in compras:
        v_pago = float(c.valor_pago)
        cpm = (v_pago / (c.quantidade / 1000)) if c.quantidade > 0 else 0
        writer.writerow([
            c.data_operacao.strftime('%d/%m/%Y'),
            c.programa,
            c.quantidade,
            f"{v_pago:.2f}".replace('.', ','),
            f"{cpm:.2f}".replace('.', ',')
        ])
    
    conteudo_csv = "\ufeff" + output.getvalue()
    response = make_response(conteudo_csv)
    filename = f"mymiles_extrato_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)