from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import os
from engine import buscar_voos_completos

# Importações para Banco de Dados e Login
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'TonMix_Secret_99' # Chave para sessões

# --- CONFIGURAÇÃO MYSQL ---
# %23 é o código para o caractere '#' na senha TonMix#25
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:TonMix%2325@localhost:3307/mymiles_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' 
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

# --- MODELO DE USUÁRIO ---
class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Aumentado para 255 para suportar hashes longos (como scrypt)
    password = db.Column(db.String(255), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Cria as tabelas no MySQL se não existirem
with app.app_context():
    db.create_all()

# --- CARREGAMENTO DO BANCO DE DADOS SNIPER (JSON) ---
ARQUIVO_JSON = 'aeroportos_sniper.json'

def carregar_base_sniper():
    if not os.path.exists(ARQUIVO_JSON):
        return []
    try:
        with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

db_aeroportos = carregar_base_sniper()

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        # strip() remove espaços e lower() padroniza para minúsculas
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
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('password')
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('E-mail já cadastrado.', 'warning')
            return redirect(url_for('cadastro'))
        
        # Gerando hash automático (scrypt por padrão no Flask moderno)
        hashed_password = generate_password_hash(senha)
        novo_usuario = User(
            nome=nome, 
            email=email, 
            password=hashed_password
        )
        
        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Conta criada com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar conta. Tente novamente.', 'danger')
            print(f"Erro no banco: {e}")
    
    return render_template('cadastro.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('login'))

# --- ROTAS DA APLICAÇÃO (PROTEGIDAS) ---

@app.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user)

@app.route('/api/aeroportos')
@login_required
def api_aeroportos():
    query = request.args.get('q', '').lower().strip()
    if not query or len(query) < 2:
        return jsonify([])

    resultados = []
    for item in db_aeroportos:
        s_key = str(item.get('search_key', '')).lower()
        if query in s_key:
            resultados.append({
                "code": item.get('code', ''),
                "name": item.get('name', ''),
                "search_key": s_key
            })
    
    resultados.sort(key=lambda x: (x['code'].lower() != query, not x['name'].lower().startswith(query)))
    return jsonify(resultados[:10])

@app.route('/buscar', methods=['POST'])
@login_required
def buscar():
    try:
        data = request.json
        res = buscar_voos_completos(
            origem=data.get('origem', '').upper().strip(),
            destino=data.get('destino', '').upper().strip(),
            data_ida=data.get('data_ida'),
            data_volta=data.get('data_volta'),
            custo_milheiro=float(data.get('custo_milheiro', 17.50)),
            pax=int(data.get('pax', 1)),
            classe=data.get('classe', 'ECONOMY')
        )
        if not res:
            return jsonify({"status": "erro", "mensagem": "Nenhum voo encontrado."})
        return jsonify({"status": "sucesso", "dados": res})
    except Exception as e:
        print(f"Erro na busca: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro interno na busca."})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)