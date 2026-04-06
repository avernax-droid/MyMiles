from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

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

class HistoricoBusca(db.Model):
    __tablename__ = 'historico_buscas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    origem_iata = db.Column(db.String(3), nullable=False)
    origem_nome = db.Column(db.String(100))
    destino_iata = db.Column(db.String(3), nullable=False)
    destino_nome = db.Column(db.String(100))
    data_ida = db.Column(db.Date, nullable=False)
    data_volta = db.Column(db.Date)
    classe = db.Column(db.String(20))
    pax = db.Column(db.Integer)
    melhor_cia = db.Column(db.String(50))
    melhor_preco_rs = db.Column(db.Numeric(10, 2))
    limite_milhas = db.Column(db.Integer)
    valor_milheiro_usado = db.Column(db.Numeric(10, 2))
    data_consulta = db.Column(db.DateTime, default=datetime.utcnow)