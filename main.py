
# ==================== IMPORTS E APP ====================
from flask import Flask, request, jsonify, Response, send_from_directory, render_template_string
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import json
import os
from datetime import datetime
import functools

CORS_ORIGINS = '*'
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# ==================== CONFIGURAÇÃO DO BANCO ====================

import urllib.parse

database_url = os.environ.get('DATABASE_URL')

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== SOCKET ====================

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Detecta se devemos usar o banco de dados (DATABASE_URL fornecido)
USING_DB = bool(database_url)

# ======= MODELS (quando USING_DB == True) =======
if USING_DB:
    planilha_categoria = db.Table(
        'planilha_categoria',
        db.Column('planilha_id', db.Integer, db.ForeignKey('planilhas.id'), primary_key=True),
        db.Column('categoria_id', db.Integer, db.ForeignKey('categorias.id'), primary_key=True)
    )

    class Categoria(db.Model):
        __tablename__ = 'categorias'
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(255), nullable=False)
        criado_em = db.Column(db.DateTime, default=datetime.utcnow)
        atualizado_em = db.Column(db.DateTime, onupdate=datetime.utcnow)

        def to_dict(self):
            return {
                'id': self.id,
                'nome': self.nome,
                'criado_em': self.criado_em.isoformat() if self.criado_em else None,
                'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
            }

    class Planilha(db.Model):
        __tablename__ = 'planilhas'
        id = db.Column(db.Integer, primary_key=True)
        titulo = db.Column(db.String(255), nullable=False)
        url = db.Column(db.String(2048), nullable=False)
        imagem = db.Column(db.String(2048), nullable=True)
        criado_em = db.Column(db.DateTime, default=datetime.utcnow)
        atualizado_em = db.Column(db.DateTime, onupdate=datetime.utcnow)
        categorias = db.relationship('Categoria', secondary=planilha_categoria, lazy='subquery', backref=db.backref('planilhas', lazy=True))

        def to_dict(self):
            return {
                'id': self.id,
                'titulo': self.titulo,
                'url': self.url,
                'imagem': self.imagem,
                'criado_em': self.criado_em.isoformat() if self.criado_em else None,
                'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
                'categorias': [c.id for c in self.categorias]
            }

    # Cria as tabelas automaticamente (seguro na inicialização)
    with app.app_context():
        db.create_all()

# ==================== FRONTEND ====================
# Rota para servir a página principal
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# ========== Associação de Planilha a Categoria ==========

# PUT - Atualizar categorias de uma planilha
@app.route('/api/planilhas/<int:planilha_id>/categorias', methods=['PUT'])
def atualizar_categorias_planilha(planilha_id):
    """Atualiza as categorias associadas a uma planilha"""
    try:
        planilhas = carregar_planilhas()
        categorias = carregar_categorias()
        idx = next((i for i, p in enumerate(planilhas) if p['id'] == planilha_id), None)
        if idx is None:
            return jsonify({'sucesso': False, 'mensagem': f'Planilha com ID {planilha_id} não encontrada'}), 404
        body = request.get_json()
        if not body or 'categorias' not in body or not isinstance(body['categorias'], list):
            return jsonify({'sucesso': False, 'mensagem': 'É necessário fornecer uma lista de IDs de categorias'}), 400
        # Filtra apenas categorias existentes
        ids_validos = [c['id'] for c in categorias]
        novas_categorias = [cid for cid in body['categorias'] if cid in ids_validos]
        planilhas[idx]['categorias'] = novas_categorias
        planilhas[idx]['atualizado_em'] = datetime.now().isoformat()
        salvar_planilhas(planilhas)
        # Emitir evento WebSocket para atualizar todos os clientes
        socketio.emit('planilha_editada', {'dado': planilhas[idx]})
        return jsonify({'sucesso': True, 'mensagem': 'Categorias da planilha atualizadas', 'dado': planilhas[idx]}), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao atualizar categorias da planilha: {str(e)}'}), 500

# Ao deletar uma categoria, também deletar TODAS as planilhas que a utilizam
def remover_categoria_de_planilhas(categoria_id):
    """
    Remove todas as planilhas associadas à categoria informada.
    Qualquer planilha que contenha esse ID em sua lista de categorias será deletada.
    """
    planilhas = carregar_planilhas()
    total_antes = len(planilhas)
    # Mantém apenas planilhas que NÃO possuem essa categoria
    planilhas_filtradas = [
        p for p in planilhas
        if not ('categorias' in p and categoria_id in p['categorias'])
    ]
    if len(planilhas_filtradas) != total_antes:
        salvar_planilhas(planilhas_filtradas)
        # Emitir evento WebSocket para atualizar todos os clientes quando planilhas são removidas
        socketio.emit('planilhas_atualizadas', {})


# ==================== CATEGORIAS ====================

# GET - Listar todas as categorias
@app.route('/api/categorias', methods=['GET'])
def listar_categorias():
    categorias = carregar_categorias()
    return jsonify({'sucesso': True, 'total': len(categorias), 'dados': categorias}), 200

# GET - Obter uma categoria específica
@app.route('/api/categorias/<int:categoria_id>', methods=['GET'])
def obter_categoria(categoria_id):
    categorias = carregar_categorias()
    categoria = next((c for c in categorias if c['id'] == categoria_id), None)
    if categoria:
        return jsonify({'sucesso': True, 'dado': categoria}), 200
    return jsonify({'sucesso': False, 'mensagem': f'Categoria com ID {categoria_id} não encontrada'}), 404

# POST - Criar uma nova categoria
@app.route('/api/categorias', methods=['POST'])
def criar_categoria():
    try:
        categorias = carregar_categorias()
        nova = request.get_json()
        if not nova or 'nome' not in nova:
            return jsonify({'sucesso': False, 'mensagem': 'Nome da categoria é obrigatório'}), 400
        novo_id = max([c['id'] for c in categorias], default=0) + 1
        nova['id'] = novo_id
        nova['criado_em'] = datetime.now().isoformat()
        categorias.append(nova)
        salvar_categorias(categorias)
        # Emitir evento WebSocket para atualizar todos os clientes
        socketio.emit('categoria_criada', {'dado': nova})
        return jsonify({'sucesso': True, 'mensagem': 'Categoria criada com sucesso', 'dado': nova}), 201
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao criar categoria: {str(e)}'}), 500

# PUT - Editar uma categoria
@app.route('/api/categorias/<int:categoria_id>', methods=['PUT'])
def editar_categoria(categoria_id):
    try:
        categorias = carregar_categorias()
        idx = next((i for i, c in enumerate(categorias) if c['id'] == categoria_id), None)
        if idx is None:
            return jsonify({'sucesso': False, 'mensagem': f'Categoria com ID {categoria_id} não encontrada'}), 404
        atualizados = request.get_json()
        if not atualizados:
            return jsonify({'sucesso': False, 'mensagem': 'Nenhum dado fornecido para atualização'}), 400
        categorias[idx].update(atualizados)
        categorias[idx]['id'] = categoria_id
        categorias[idx]['atualizado_em'] = datetime.now().isoformat()
        salvar_categorias(categorias)
        # Emitir evento WebSocket para atualizar todos os clientes
        socketio.emit('categoria_editada', {'dado': categorias[idx]})
        return jsonify({'sucesso': True, 'mensagem': 'Categoria atualizada com sucesso', 'dado': categorias[idx]}), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao editar categoria: {str(e)}'}), 500

# DELETE - Deletar uma categoria
@app.route('/api/categorias/<int:categoria_id>', methods=['DELETE'])
def deletar_categoria(categoria_id):
    try:
        categorias = carregar_categorias()
        idx = next((i for i, c in enumerate(categorias) if c['id'] == categoria_id), None)
        if idx is None:
            return jsonify({'sucesso': False, 'mensagem': f'Categoria com ID {categoria_id} não encontrada'}), 404
        removida = categorias.pop(idx)
        salvar_categorias(categorias)
        # Remover referência da categoria das planilhas
        remover_categoria_de_planilhas(categoria_id)
        # Emitir evento WebSocket para atualizar todos os clientes
        socketio.emit('categoria_deletada', {'id': categoria_id})
        return jsonify({'sucesso': True, 'mensagem': 'Categoria deletada com sucesso', 'dado': removida}), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao deletar categoria: {str(e)}'}), 500

# DELETE - Deletar todas as categorias
@app.route('/api/categorias', methods=['DELETE'])
def deletar_todas_categorias():
    try:
        salvar_categorias([])
        return jsonify({'sucesso': True, 'mensagem': 'Todas as categorias foram deletadas'}), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao deletar categorias: {str(e)}'}), 500



# Arquivos de armazenamento
PLANILHAS_FILE = 'dados.json'  # Mantém o nome para compatibilidade
CATEGORIAS_FILE = 'categorias.json'


# Funções utilitárias para planilhas
def carregar_planilhas():
    """Carrega planilhas.

    Se `USING_DB` for True, carrega do banco via SQLAlchemy; caso contrário
    carrega do arquivo JSON antigo para manter compatibilidade.
    """
    if USING_DB:
        try:
            return [p.to_dict() for p in Planilha.query.order_by(Planilha.id).all()]
        except Exception:
            return []

    if not os.path.exists(PLANILHAS_FILE):
        return []

    try:
        with open(PLANILHAS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def salvar_planilhas(planilhas):
    if USING_DB:
        # Substitui todas as planilhas no banco pelos dados fornecidos.
        try:
            # Apaga todas as planilhas (associações serão limpas automaticamente)
            Planilha.query.delete()
            db.session.commit()
            for p in planilhas:
                categorias_ids = p.get('categorias', []) or []
                nova = Planilha(
                    id=p.get('id'),
                    titulo=p.get('titulo'),
                    url=p.get('url'),
                    imagem=p.get('imagem') if 'imagem' in p else None,
                )
                # associa categorias existentes
                for cid in categorias_ids:
                    cat = Categoria.query.get(cid)
                    if cat:
                        nova.categorias.append(cat)
                db.session.add(nova)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return

    with open(PLANILHAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(planilhas, f, ensure_ascii=False, indent=2)

# Funções utilitárias para categorias
def carregar_categorias():
    """Carrega categorias. Se `USING_DB` for True, consulta o banco.
    Caso contrário, faz fallback para o arquivo JSON.
    """
    if USING_DB:
        try:
            return [c.to_dict() for c in Categoria.query.order_by(Categoria.id).all()]
        except Exception:
            return []

    if not os.path.exists(CATEGORIAS_FILE):
        return []

    try:
        with open(CATEGORIAS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def salvar_categorias(categorias):
    if USING_DB:
        try:
            Categoria.query.delete()
            db.session.commit()
            for c in categorias:
                nova = Categoria(id=c.get('id'), nome=c.get('nome'))
                # tenta preservar timestamps se existirem
                if 'criado_em' in c and c['criado_em']:
                    try:
                        nova.criado_em = datetime.fromisoformat(c['criado_em'])
                    except Exception:
                        pass
                db.session.add(nova)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return

    with open(CATEGORIAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(categorias, f, ensure_ascii=False, indent=2)


# Endpoint auxiliar: migra os arquivos JSON atuais para o banco (quando aplicável)
@app.route('/api/migrate', methods=['POST'])
def migrate_json_to_db():
    if not USING_DB:
        return jsonify({'sucesso': False, 'mensagem': 'DATABASE_URL não configurado; migração não necessária'}), 400
    try:
        # importa categorias
        raw_cats = []
        if os.path.exists(CATEGORIAS_FILE):
            with open(CATEGORIAS_FILE, 'r', encoding='utf-8') as f:
                raw_cats = json.load(f) or []
        # importa planilhas
        raw_pls = []
        if os.path.exists(PLANILHAS_FILE):
            with open(PLANILHAS_FILE, 'r', encoding='utf-8') as f:
                raw_pls = json.load(f) or []

        # Salva categorias e planilhas usando as funções DB-aware
        salvar_categorias(raw_cats)
        salvar_planilhas(raw_pls)
        return jsonify({'sucesso': True, 'mensagem': 'Migração concluída', 'categorias': len(raw_cats), 'planilhas': len(raw_pls)}), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro na migração: {str(e)}'}), 500

# ==================== ROTAS ====================


# ==================== PLANILHAS ====================

# GET - Listar todas as planilhas
@app.route('/api/planilhas', methods=['GET'])
def listar_planilhas():
    """Lista todas as planilhas"""
    planilhas = carregar_planilhas()
    return jsonify({
        'sucesso': True,
        'total': len(planilhas),
        'dados': planilhas
    }), 200


# GET - Obter uma planilha específica por ID
@app.route('/api/planilhas/<int:planilha_id>', methods=['GET'])
def obter_planilha(planilha_id):
    """Obtém uma planilha específica pelo ID"""
    planilhas = carregar_planilhas()
    planilha = next((p for p in planilhas if p['id'] == planilha_id), None)
    if planilha:
        return jsonify({'sucesso': True, 'dado': planilha}), 200
    return jsonify({'sucesso': False, 'mensagem': f'Planilha com ID {planilha_id} não encontrada'}), 404


# POST - Criar uma nova planilha
@app.route('/api/planilhas', methods=['POST'])
def criar_planilha():
    """Cria uma nova planilha (card)"""
    try:
        planilhas = carregar_planilhas()
        nova = request.get_json()
        if not nova or 'titulo' not in nova or 'url' not in nova:
            return jsonify({'sucesso': False, 'mensagem': 'Título e URL são obrigatórios'}), 400
        novo_id = max([p['id'] for p in planilhas], default=0) + 1
        nova['id'] = novo_id
        nova['criado_em'] = datetime.now().isoformat()
        # Permite categorias opcionais (lista de ids)
        if 'categorias' not in nova:
            nova['categorias'] = []
        planilhas.append(nova)
        salvar_planilhas(planilhas)
        # Emitir evento WebSocket para atualizar todos os clientes
        socketio.emit('planilha_criada', {'dado': nova})
        return jsonify({'sucesso': True, 'mensagem': 'Planilha criada com sucesso', 'dado': nova}), 201
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao criar planilha: {str(e)}'}), 500


# PUT - Editar uma planilha
@app.route('/api/planilhas/<int:planilha_id>', methods=['PUT'])
def editar_planilha(planilha_id):
    """Edita uma planilha existente"""
    try:
        planilhas = carregar_planilhas()
        idx = next((i for i, p in enumerate(planilhas) if p['id'] == planilha_id), None)
        if idx is None:
            return jsonify({'sucesso': False, 'mensagem': f'Planilha com ID {planilha_id} não encontrada'}), 404
        atualizados = request.get_json()
        if not atualizados:
            return jsonify({'sucesso': False, 'mensagem': 'Nenhum dado fornecido para atualização'}), 400
        planilhas[idx].update(atualizados)
        planilhas[idx]['id'] = planilha_id
        planilhas[idx]['atualizado_em'] = datetime.now().isoformat()
        salvar_planilhas(planilhas)
        # Emitir evento WebSocket para atualizar todos os clientes
        socketio.emit('planilha_editada', {'dado': planilhas[idx]})
        return jsonify({'sucesso': True, 'mensagem': 'Planilha atualizada com sucesso', 'dado': planilhas[idx]}), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao editar planilha: {str(e)}'}), 500


# DELETE - Deletar uma planilha
@app.route('/api/planilhas/<int:planilha_id>', methods=['DELETE'])
def deletar_planilha(planilha_id):
    """Deleta uma planilha"""
    try:
        planilhas = carregar_planilhas()
        idx = next((i for i, p in enumerate(planilhas) if p['id'] == planilha_id), None)
        if idx is None:
            return jsonify({'sucesso': False, 'mensagem': f'Planilha com ID {planilha_id} não encontrada'}), 404
        removida = planilhas.pop(idx)
        salvar_planilhas(planilhas)
        # Emitir evento WebSocket para atualizar todos os clientes
        socketio.emit('planilha_deletada', {'id': planilha_id})
        return jsonify({'sucesso': True, 'mensagem': 'Planilha deletada com sucesso', 'dado': removida}), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao deletar planilha: {str(e)}'}), 500


# DELETE - Deletar todas as planilhas
@app.route('/api/planilhas', methods=['DELETE'])
def deletar_todas_planilhas():
    """Deleta todas as planilhas"""
    try:
        salvar_planilhas([])
        return jsonify({'sucesso': True, 'mensagem': 'Todas as planilhas foram deletadas'}), 200
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao deletar planilhas: {str(e)}'}), 500


# ==================== ENDPOINT DE TESTE ====================

@app.route('/api/teste', methods=['GET'])
def teste():
    """Endpoint simples para verificar se a API está no ar."""
    return jsonify(
        {
            'sucesso': True,
            'mensagem': 'API em funcionamento',
            'timestamp': datetime.now().isoformat()
        }
    ), 200


# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    # Evita UnicodeEncodeError no Windows (console cp1252) por causa de emojis
    print("Servidor iniciado em http://localhost:5000")
    print("\nEndpoints disponíveis:")
    print("  PLANILHAS:")
    print("    GET    /api/planilhas                 - Listar todas as planilhas")
    print("    GET    /api/planilhas/<id>            - Obter uma planilha específica")
    print("    POST   /api/planilhas                 - Criar uma nova planilha")
    print("    PUT    /api/planilhas/<id>            - Editar uma planilha")
    print("    DELETE /api/planilhas/<id>            - Deletar uma planilha")
    print("    DELETE /api/planilhas                 - Deletar todas as planilhas")
    print("    PUT    /api/planilhas/<id>/categorias - Atualizar categorias da planilha")
    print("\n  CATEGORIAS:")
    print("    GET    /api/categorias                - Listar todas as categorias")
    print("    GET    /api/categorias/<id>           - Obter uma categoria específica")
    print("    POST   /api/categorias                - Criar uma nova categoria")
    print("    PUT    /api/categorias/<id>           - Editar uma categoria")
    print("    DELETE /api/categorias/<id>           - Deletar uma categoria")
    print("    DELETE /api/categorias                - Deletar todas as categorias")
    print("\n  OUTROS:")
    print("    GET    /api/teste                     - Testar a API\n")
    print("  WEBSOCKETS:")
    print("    Conecta automaticamente para atualizações em tempo real\n")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
