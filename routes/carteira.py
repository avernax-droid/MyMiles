from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from datetime import datetime
import csv
import io
from models import db, Aquisicao
from flask_login import login_required, current_user
from utils.helpers import converter_moeda_para_float

# Criando o Blueprint
carteira_bp = Blueprint('carteira', __name__)

@carteira_bp.route('/carteira', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        try:
            valor_final = converter_moeda_para_float(request.form.get('valor_pago'))
            nova = Aquisicao(
                user_id=current_user.id,
                programa=request.form.get('programa'),
                quantidade=int(request.form.get('quantidade')),
                valor_pago=valor_final,
                data_operacao=datetime.strptime(request.form.get('data_compra'), '%Y-%m-%d')
            )
            db.session.add(nova)
            db.session.commit()
            flash("Lançamento salvo!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {e}", "danger")
        return redirect(url_for('carteira.index'))

    compras = Aquisicao.query.filter_by(user_id=current_user.id).order_by(Aquisicao.data_operacao.asc()).all()
    investimento_total = sum(float(c.valor_pago) for c in compras)
    saldo_total = sum(c.quantidade for c in compras)
    
    milhas_processadas = []
    for c in compras:
        v_pago = float(c.valor_pago)
        cpm = (v_pago / (c.quantidade / 1000)) if c.quantidade > 0 else 0
        milhas_processadas.append({
            'id': c.id,
            'data': c.data_operacao.strftime('%d/%m/%Y'),
            'data_raw': c.data_operacao.strftime('%Y-%m-%d'),
            'programa': c.programa,
            'quantidade': c.quantidade,
            'valor_pago': v_pago,
            'cpm': cpm
        })

    cpm_geral = (investimento_total / (saldo_total / 1000)) if saldo_total > 0 else 0
    return render_template('carteira.html', user=current_user, milhas=milhas_processadas, investimento=investimento_total, saldo=saldo_total, cpm_geral=cpm_geral)

@carteira_bp.route('/carteira/editar/<int:id>', methods=['POST'])
@login_required
def editar(id):
    item = Aquisicao.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        valor_final = converter_moeda_para_float(request.form.get('valor_pago'))
        item.programa = request.form.get('programa')
        item.quantidade = int(request.form.get('quantidade'))
        item.valor_pago = valor_final
        item.data_operacao = datetime.strptime(request.form.get('data_compra'), '%Y-%m-%d')
        db.session.commit()
        flash("Alteração realizada!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro: {e}", "danger")
    return redirect(url_for('carteira.index'))

@carteira_bp.route('/carteira/deletar/<int:id>', methods=['POST'])
@login_required
def deletar(id):
    item = Aquisicao.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        db.session.delete(item)
        db.session.commit()
        flash("Entrada excluída.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro: {e}", "danger")
    return redirect(url_for('carteira.index'))

@carteira_bp.route('/carteira/exportar')
@login_required
def exportar():
    compras = Aquisicao.query.filter_by(user_id=current_user.id).order_by(Aquisicao.data_operacao.asc()).all()
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