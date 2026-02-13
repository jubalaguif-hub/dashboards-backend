
# ==================== IMPORTS E APP ====================
from flask import Flask, request, jsonify, Response, send_from_directory, render_template_string
from flask_cors import CORS
import json
import os
from datetime import datetime
import functools

CORS_ORIGINS = '*'
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

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
    """Carrega a lista de planilhas a partir do arquivo JSON.

    Em caso de arquivo inexistente ou JSON inválido, retorna uma lista vazia
    em vez de quebrar o servidor.
    """
    if not os.path.exists(PLANILHAS_FILE):
        return []

    try:
        with open(PLANILHAS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Arquivo corrompido ou vazio: faz fallback seguro
        return []

def salvar_planilhas(planilhas):
    with open(PLANILHAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(planilhas, f, ensure_ascii=False, indent=2)

# Funções utilitárias para categorias
def carregar_categorias():
    """Carrega a lista de categorias a partir do arquivo JSON.

    Em caso de arquivo inexistente ou JSON inválido, retorna uma lista vazia
    em vez de quebrar o servidor.
    """
    if not os.path.exists(CATEGORIAS_FILE):
        return []

    try:
        with open(CATEGORIAS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Arquivo corrompido ou vazio: faz fallback seguro
        return []

def salvar_categorias(categorias):
    with open(CATEGORIAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(categorias, f, ensure_ascii=False, indent=2)

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
    print("🚀 Servidor iniciado em http://localhost:5000")
    print("\n📚 Endpoints disponíveis:")
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
    app.run(debug=True, host='0.0.0.0', port=5000)
