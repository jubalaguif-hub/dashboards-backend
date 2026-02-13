# Gestão de Planilhas e Categorias – Back-end

API em Flask para gerenciar **planilhas (dashboards)** e **categorias**, usada pelo front-end hospedado no GitHub Pages.

Repositório: `https://github.com/jubalaguif-hub/dashboards-backend`

---

## Tecnologias

- Python 3.11+
- Flask
- Flask-CORS
- Gunicorn (produção, Render)
- Armazenamento em arquivos JSON (`dados.json` e `categorias.json`)

---

## Estrutura do projeto

- `main.py` – aplicação Flask com todas as rotas da API e o servidor.
- `requirements.txt` – dependências Python.
- `dados.json` – armazenamento das planilhas (cards).
- `categorias.json` – armazenamento das categorias.
- `static/` – versão embutida do front-end (para rodar tudo local).

---

## Como rodar localmente

1. (Opcional, mas recomendado) criar e ativar um ambiente virtual:

   ```bash
   cd Back-end
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

2. Instalar as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Executar o servidor Flask em modo de desenvolvimento:

   ```bash
   python main.py
   ```

4. Acessar:

   - Front-end local: `http://localhost:5000/`
   - Teste rápido da API: `http://localhost:5000/api/teste`

Os arquivos `dados.json` e `categorias.json` serão lidos/gravados no diretório raiz do projeto.

---

## Endpoints principais

### Planilhas

- `GET /api/planilhas` – lista todas as planilhas.
- `GET /api/planilhas/<id>` – obtém uma planilha específica.
- `POST /api/planilhas` – cria uma planilha.
- `PUT /api/planilhas/<id>` – edita uma planilha.
- `DELETE /api/planilhas/<id>` – remove uma planilha.
- `DELETE /api/planilhas` – remove todas as planilhas.
- `PUT /api/planilhas/<id>/categorias` – atualiza as categorias ligadas a uma planilha.

### Categorias

- `GET /api/categorias` – lista todas as categorias.
- `GET /api/categorias/<id>` – obtém uma categoria específica.
- `POST /api/categorias` – cria uma categoria.
- `PUT /api/categorias/<id>` – edita uma categoria.
- `DELETE /api/categorias/<id>` – remove uma categoria.
- `DELETE /api/categorias` – remove todas as categorias.

### Outros

- `GET /api/teste` – verifica se a API está no ar.

---

## Deploy no Render

Este projeto foi preparado para rodar no [Render](https://render.com/).

### Configuração usada

- **Build Command**

  ```bash
  pip install -r requirements.txt
  ```

- **Start Command**

  ```bash
  gunicorn main:app
  ```

### URL pública

Depois do deploy, a API fica acessível em:

```text
https://dashboards-backend-m8mv.onrender.com
```

Exemplo de teste:

```text
https://dashboards-backend-1o4j.onrender.com/api/teste
```

---

## Integração com o front-end

O front-end (repositório `dashboards-frontend`) configura a URL da API em `index.html`:

```html
<script>
  // Backend publicado no Render
  window.API_BASE_URL = 'https://dashboards-backend-m8mv.onrender.com';
</script>
```

Assim, qualquer usuário acessando o GitHub Pages do front consome os dados desta API.


