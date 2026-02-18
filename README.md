# Gestão de Planilhas e Categorias – Back-end

API em Flask para gerenciar **planilhas (dashboards)** e **categorias**, usada pelo front-end hospedado no GitHub Pages.

Repositório: `https://github.com/jubalaguif-hub/dashboards-backend`

---

## Tecnologias

- Python 3.11+ (compatível com 3.14)
- Flask
- Flask-CORS
- Flask-SocketIO (atualizações em tempo real via WebSocket)
- Gunicorn (produção, Render)
- Gevent (servidor assíncrono para WebSockets)
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

### WebSockets (Atualizações em Tempo Real)

O servidor utiliza WebSockets para sincronizar mudanças entre todos os clientes conectados em tempo real. Quando uma categoria ou planilha é criada, editada ou deletada em um navegador, todos os outros navegadores conectados recebem a atualização automaticamente.

**Eventos emitidos:**
- `categoria_criada` – quando uma nova categoria é criada
- `categoria_editada` – quando uma categoria é editada
- `categoria_deletada` – quando uma categoria é deletada
- `planilha_criada` – quando uma nova planilha é criada
- `planilha_editada` – quando uma planilha é editada
- `planilha_deletada` – quando uma planilha é deletada

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
  socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
  ```

  **Nota:** O uso de `gevent` é necessário para suportar WebSockets. O parâmetro `-w 1` limita a um worker para evitar problemas de concorrência com arquivos JSON. `--worker-connections 1000` permite múltiplas conexões WebSocket simultâneas.

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

## Configurar PostgreSQL (Render)

Se você criou um banco PostgreSQL no Render, adicione a variável de ambiente `DATABASE_URL` no painel do serviço (Environment → Environment Variables). Use a connection string fornecida pelo Render, por exemplo:

```
postgresql://admin:UKDds98V5s7BbXfSxMHo5XMYyqixfcj0@dpg-d6auho0boq4c73dlca90-a.virginia-postgres.render.com/planilhas_db
```

Notas importantes:
- O código já converte automaticamente `postgres://` para `postgresql://` quando necessário.
- Ao iniciar com `DATABASE_URL` presente, o back-end criará as tabelas automaticamente usando SQLAlchemy.
- Não comite credenciais no repositório.

## Migrar dados JSON locais para o banco

Após adicionar `DATABASE_URL` e realizar o redeploy do serviço no Render, importe os dados locais (`categorias.json` e `dados.json`) para o banco executando o endpoint de migração:

Requisição (exemplo):

```bash
curl -X POST https://<seu-app>.onrender.com/api/migrate -H "Content-Type: application/json"
```

O endpoint retornará um JSON indicando quantas categorias e planilhas foram importadas.

## Testes e verificação

- Verificar se a API está no ar:

```bash
curl https://<seu-app>.onrender.com/api/teste
```

- Listar categorias (após a migração):

```bash
curl https://<seu-app>.onrender.com/api/categorias
```

## Testar localmente com o mesmo banco

No Windows PowerShell você pode definir a variável de ambiente e iniciar a app localmente:

```powershell
$env:DATABASE_URL = 'postgresql://admin:...@.../planilhas_db'
python main.py
```

Isso faz com que a aplicação use o PostgreSQL remoto localmente (útil para testes). Se `DATABASE_URL` não estiver definida, a aplicação continuará usando os arquivos `dados.json` e `categorias.json` como fallback.


## Integração com o front-end

O front-end (repositório `dashboards-frontend`) configura a URL da API em `index.html`:

```html
<script>
  // Backend publicado no Render
  window.API_BASE_URL = 'https://dashboards-backend-m8mv.onrender.com';
</script>
```

Assim, qualquer usuário acessando o GitHub Pages do front consome os dados desta API.



