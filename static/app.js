// ========== MODAL ===========
const modalBg = document.getElementById('modal-bg');
const modal = modalBg ? modalBg.querySelector('.modal') : null;
const modalTitulo = modalBg ? modalBg.querySelector('#modal-titulo') : null;
const modalCampos = modalBg ? modalBg.querySelector('.modal-campos') : null;
const modalForm = modalBg ? modalBg.querySelector('#modal-form') : null;
const modalBtnCancelar = modalBg ? modalBg.querySelector('.modal-cancelar') : null;
const modalBtnClose = modalBg ? modalBg.querySelector('#modal-close') : null;
let modalCallback = null;

function abrirModal({ titulo, campos, onConfirm }) {
  if (!modalBg) return;
  modalTitulo.textContent = titulo;
  modalCampos.innerHTML = '';
  // Garante que os botões padrão (Salvar/Cancelar) estejam visíveis e resetados
  if (modalForm) {
    const botoesFooter = modalForm.querySelector('.modal-botoes');
    const btnSalvar = modalForm.querySelector('.modal-salvar');
    if (botoesFooter) {
      botoesFooter.style.display = 'flex';
    }
    if (btnSalvar) {
      btnSalvar.textContent = 'Salvar';
      btnSalvar.disabled = false;
    }
  }
  campos.forEach(c => {
    const label = document.createElement('label');
    label.textContent = c.label;
    label.style.marginBottom = '0.2rem';
    const input = document.createElement(c.type === 'select' ? 'select' : 'input');
    if (c.type !== 'select') {
      input.type = c.type || 'text';
      input.value = c.value || '';
      input.placeholder = c.placeholder || '';
    } else {
      (c.options || []).forEach(opt => {
        const o = document.createElement('option');
        o.value = opt.value;
        o.textContent = opt.label;
        if (c.value == opt.value) o.selected = true;
        input.appendChild(o);
      });
    }
    input.name = c.name;
    input.required = !!c.required;
    input.style.marginBottom = '0.5rem';
    label.appendChild(input);
    modalCampos.appendChild(label);
  });
  modalBg.style.display = 'flex';
  setTimeout(() => modal.classList.add('show'), 10);
  modalCallback = onConfirm;
}

function fecharModal() {
  if (!modalBg) return;
  modal.classList.remove('show');
  setTimeout(() => { 
    modalBg.style.display = 'none';
    // Resetar texto do botão salvar
    if (modalForm && modalForm.querySelector('.modal-salvar')) {
      modalForm.querySelector('.modal-salvar').textContent = 'Salvar';
    }
  }, 200);
  modalCallback = null;
}

if (modalBtnCancelar) modalBtnCancelar.onclick = fecharModal;
if (modalBtnClose) modalBtnClose.onclick = fecharModal;
if (modalBg) modalBg.onclick = (e) => { if (e.target === modalBg) fecharModal(); };
if (modalForm) {
  modalForm.onsubmit = (e) => {
    e.preventDefault();
    if (modalCallback) {
      const data = {};
      Array.from(modalCampos.querySelectorAll('input,select')).forEach(inp => {
        data[inp.name] = inp.value;
      });
      modalCallback(data);
    }
    fecharModal();
  };
}
// Funções para consumir a API e animar a interface
// Permite configurar a URL base da API via window.API_BASE_URL (ex.: 'https://seu-backend.onrender.com')
const API_BASE_URL = (typeof window !== 'undefined' && window.API_BASE_URL) ? window.API_BASE_URL : '';

const api = {
  categorias: `${API_BASE_URL}/api/categorias`,
  planilhas: `${API_BASE_URL}/api/planilhas`
};

// ========== CATEGORIAS ==========
async function carregarCategorias() {
  const res = await fetch(api.categorias);
  const data = await res.json();
  return data.dados || [];
}

async function criarCategoria(nome) {
  try {
    const res = await fetch(api.categorias, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nome })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.mensagem || 'Erro ao criar categoria');
    return data;
  } catch (e) {
    alert(e.message);
    throw e;
  }
}

async function editarCategoria(id, nome) {
  try {
    const res = await fetch(`${api.categorias}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nome })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.mensagem || 'Erro ao editar categoria');
    return data;
  } catch (e) {
    alert(e.message);
    throw e;
  }
}

async function deletarCategoria(id) {
  try {
    const res = await fetch(`${api.categorias}/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.mensagem || 'Erro ao deletar categoria');
    return data;
  } catch (e) {
    alert(e.message);
    throw e;
  }
}

// ========== PLANILHAS ==========
async function carregarPlanilhas() {
  const res = await fetch(api.planilhas);
  const data = await res.json();
  return data.dados || [];
}

// Criar planilha (agora com campo opcional de imagem)
async function criarPlanilha(titulo, url, categoriaId, imagem) {
  try {
    const body = {
      titulo,
      url,
      categorias: categoriaId ? [parseInt(categoriaId)] : []
    };

    // Campo opcional de imagem (URL completa ou caminho /img/arquivo.png)
    if (imagem && imagem.trim()) {
      body.imagem = imagem.trim();
    }

    const res = await fetch(api.planilhas, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.mensagem || 'Erro ao criar planilha');
    return data;
  } catch (e) {
    alert(e.message);
    throw e;
  }
}

// Editar planilha (campo opcional de imagem também pode ser alterado)
async function editarPlanilha(id, titulo, url, categoriaId, imagem) {
  try {
    const body = {
      titulo,
      url,
      categorias: categoriaId ? [parseInt(categoriaId)] : []
    };

    if (imagem !== undefined) {
      if (imagem && imagem.trim()) {
        body.imagem = imagem.trim();
      } else {
        // Se vier vazio, zera o campo imagem
        body.imagem = '';
      }
    }

    const res = await fetch(`${api.planilhas}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.mensagem || 'Erro ao editar planilha');
    return data;
  } catch (e) {
    alert(e.message);
    throw e;
  }
}

async function deletarPlanilha(id) {
  try {
    const res = await fetch(`${api.planilhas}/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.mensagem || 'Erro ao deletar planilha');
    return data;
  } catch (e) {
    alert(e.message);
    throw e;
  }
}

// ========== DOM E EVENTOS ==========
const listaPlanilhas = document.getElementById('lista-planilhas');
const selectCategoria = document.getElementById('categoria-planilha');
const sidebarCategorias = document.getElementById('sidebar-categorias');
const sidebarEditBtn = document.querySelector('.sidebar-edit');
const sidebarAddBtn = document.querySelector('.sidebar-add');
const sidebarDelBtn = document.querySelector('.sidebar-delete');
const searchInput = document.querySelector('.search');

let categoriasSelecionadas = [];
let termoPesquisa = '';

// Event listener para pesquisa de planilhas
if (searchInput) {
  searchInput.addEventListener('input', (e) => {
    termoPesquisa = e.target.value.toLowerCase().trim();
    atualizarPlanilhas();
  });
}

sidebarEditBtn.onclick = async () => {
  const categorias = await carregarCategorias();
  if (categoriasSelecionadas.length === 0) {
    alert('Selecione uma categoria para editar');
    return;
  }
  const catId = categoriasSelecionadas[0];
  const cat = categorias.find(c => c.id === catId);
  if (!cat) return;
  
  abrirModal({
    titulo: 'Editar Categoria',
    campos: [
      { label: 'Nome', name: 'nome', value: cat.nome, required: true }
    ],
    onConfirm: async (dados) => {
      if (dados.nome && dados.nome.trim() && dados.nome !== cat.nome) {
        try {
          await editarCategoria(cat.id, dados.nome.trim());
          categoriasSelecionadas = [];
          atualizarCategorias();
          atualizarPlanilhas();
        } catch (e) {
          console.error(e);
        }
      }
    }
  });
};

sidebarDelBtn.onclick = async () => {
  if (categoriasSelecionadas.length === 0) {
    alert('Selecione uma categoria para deletar');
    return;
  }
  const categorias = await carregarCategorias();
  const catId = categoriasSelecionadas[0];
  const cat = categorias.find(c => c.id === catId);
  if (!cat) return;
  
  abrirModal({
    titulo: 'Deletar Categoria',
    campos: [],
    onConfirm: async () => {
      try {
        await deletarCategoria(cat.id);
        categoriasSelecionadas = [];
        atualizarCategorias();
        atualizarPlanilhas();
      } catch (e) {
        console.error(e);
      }
    }
  });
  
  setTimeout(() => {
    if (modalCampos) {
      modalCampos.innerHTML = `<div style="text-align:center;font-size:1.1rem;color:#e53935;margin-bottom:1.2rem;">Tem certeza que deseja deletar a categoria <b>${cat.nome}</b>?</div>`;
    }
    if (modalForm) {
      const btnSalvar = modalForm.querySelector('.modal-salvar');
      if (btnSalvar) btnSalvar.textContent = 'Deletar';
    }
  }, 10);
};

// Formulário removido - criação de planilha agora acontece via modal

async function atualizarCategorias() {
  const categorias = await carregarCategorias();
  
  // Atualiza select
  selectCategoria.innerHTML = '<option value="">Selecione a categoria</option>';
  categorias.forEach(cat => {
    selectCategoria.innerHTML += `<option value="${cat.id}">${cat.nome}</option>`;
  });
  
  // Atualiza sidebar
  sidebarCategorias.innerHTML = '';
  categorias.forEach(cat => {
    const div = document.createElement('div');
    div.className = 'sidebar-categoria-item';
    div.textContent = cat.nome;
    div.style.cursor = 'pointer';
    div.onclick = () => {
      // Toggle: permite selecionar/deselecionar uma categoria
      if (categoriasSelecionadas.includes(cat.id)) {
        categoriasSelecionadas = [];
      } else {
        categoriasSelecionadas = [cat.id];
      }
      atualizarCategorias();
      atualizarPlanilhas();
    };
    if (categoriasSelecionadas.includes(cat.id)) {
      div.style.background = '#F4A623';
      div.style.color = '#111';
    }
    sidebarCategorias.appendChild(div);
  });
}

async function atualizarPlanilhas() {
  const planilhas = await carregarPlanilhas();
  const categorias = await carregarCategorias();
  
  // Filtrar planilhas pela pesquisa primeiro (pesquisa tem prioridade)
  let planilhasFiltradas = [];
  
  if (termoPesquisa.length > 0) {
    // Se houver pesquisa, mostrar de TODAS as categorias
    planilhasFiltradas = planilhas.filter(p =>
      p.titulo.toLowerCase().includes(termoPesquisa)
    );
  } else if (categoriasSelecionadas.length > 0) {
    // Se não houver pesquisa, filtrar pela categoria selecionada
    const categoriaId = categoriasSelecionadas[0];
    planilhasFiltradas = planilhas.filter(p => 
      p.categorias && p.categorias.includes(categoriaId)
    );
  } else {
    // Sem pesquisa e sem categoria selecionada: não mostra nada para evitar confusão
    planilhasFiltradas = [];
  }
  
  listaPlanilhas.innerHTML = '';
  
  // Se nenhuma planilha encontrada
  if (planilhasFiltradas.length === 0) {
    const divVazio = document.createElement('div');
    divVazio.style.cssText = 'grid-column: 1 / -1; text-align: center; color: #999; padding: 3rem; font-size: 1.1rem;';
    
    if (termoPesquisa.length > 0) {
      divVazio.textContent = `Nenhuma planilha encontrada para "${termoPesquisa}"`;
    } else if (categoriasSelecionadas.length > 0) {
      divVazio.textContent = 'Nenhuma planilha nesta categoria';
    } else {
      divVazio.textContent = 'Selecione uma categoria no menu à esquerda para ver as planilhas';
    }
    
    listaPlanilhas.appendChild(divVazio);
    return;
  }
  
  planilhasFiltradas.forEach(planilha => {
    const div = document.createElement('div');
    div.className = 'card planilha';

    // Se a planilha tiver imagem definida, usa a imagem ocupando todo o card.
    // Se não tiver, o gradiente padrão do CSS (.card e nth-child) é usado automaticamente.
    if (planilha.imagem && typeof planilha.imagem === 'string' && planilha.imagem.trim() !== '') {
      const imgUrl = planilha.imagem.trim();
      div.style.backgroundImage = `url('${imgUrl}')`;
      div.style.backgroundSize = 'cover';
      div.style.backgroundPosition = 'center';
      div.style.backgroundRepeat = 'no-repeat';
    }
    div.onclick = () => window.open(planilha.url, '_blank');
    const tituloEl = document.createElement('span');
    tituloEl.className = 'titulo';
    tituloEl.textContent = planilha.titulo;
    div.appendChild(tituloEl);
    // Mostra a primeira categoria associada (se houver) apenas quando há pesquisa
    if (termoPesquisa.length > 0 && planilha.categorias && planilha.categorias.length > 0) {
      const catId = planilha.categorias[0];
      const cat = categorias.find(c => c.id === catId);
      if (cat) {
        const span = document.createElement('span');
        span.className = 'categoria';
        span.textContent = cat.nome;
        div.appendChild(span);
      }
    }
    // Botões de ação (mantidos invisíveis; usados pelos modais)
    const acoes = document.createElement('div');
    acoes.className = 'acoes';
    acoes.style.display = 'none';
    // Editar
    const btnEdit = document.createElement('button');
    btnEdit.className = 'editar';
    btnEdit.title = 'Editar';
    btnEdit.innerHTML = '<svg width="18" height="18"><use href="#edit" /></svg>';
    btnEdit.onclick = (e) => {
      e.stopPropagation();
      abrirModal({
        titulo: 'Editar planilha',
        campos: [
          { label: 'Título', name: 'titulo', value: planilha.titulo, required: true },
          { label: 'URL', name: 'url', value: planilha.url, required: true, type: 'url' },
          {
            label: 'Imagem do card (URL ou /img/arquivo.png) - opcional',
            name: 'imagem',
            value: planilha.imagem || '',
            required: false,
            placeholder: 'Ex: https://... ou /img/minha-foto.png'
          },
          {
            label: 'Categoria', name: 'categoriaId', type: 'select', value: planilha.categorias && planilha.categorias[0] ? planilha.categorias[0] : '',
            options: [{ value: '', label: 'Selecione' }].concat(categorias.map(c => ({ value: c.id, label: c.nome })))
          }
        ],
        onConfirm: async (dados) => {
          await editarPlanilha(
            planilha.id,
            dados.titulo,
            dados.url,
            dados.categoriaId,
            dados.imagem
          );
          atualizarPlanilhas();
        }
      });
    };
    // Deletar
    const btnDel = document.createElement('button');
    btnDel.className = 'deletar';
    btnDel.title = 'Deletar';
    btnDel.innerHTML = '<svg width="18" height="18"><use href="#delete" /></svg>';
    btnDel.onclick = (e) => {
      e.stopPropagation();
      abrirModal({
        titulo: 'Deletar planilha',
        campos: [
          { label: 'Tem certeza que deseja deletar?', name: 'confirm', value: '', type: 'hidden' }
        ],
        onConfirm: async () => {
          await deletarPlanilha(planilha.id);
          atualizarPlanilhas();
        }
      });
      // Personaliza o modal para confirmação
      setTimeout(() => {
        if (modalCampos) {
          modalCampos.innerHTML = '<div style="text-align:center;font-size:1.1rem;color:#e53935;margin-bottom:1.2rem;">Tem certeza que deseja deletar a planilha <b>' + planilha.titulo + '</b>?</div>';
        }
        if (modalForm) {
          const btnSalvar = modalForm.querySelector('.modal-salvar');
          if (btnSalvar) btnSalvar.textContent = 'Deletar';
        }
      }, 10);
    };
    acoes.appendChild(btnEdit);
    acoes.appendChild(btnDel);
    div.appendChild(acoes);

    // Botão de configurações (engrenagem) alinhado à direita, na parte de baixo do card
    const headerActions = document.createElement('div');
    headerActions.className = 'card-header-actions';
    const configBtn = document.createElement('button');
    configBtn.className = 'card-config-btn';
    configBtn.title = 'Opções da planilha';
    configBtn.innerHTML = '<svg width="18" height="18"><use href="#settings" /></svg>';
    configBtn.onclick = (e) => {
      e.stopPropagation();
      // Abre um modal com as opções de Editar e Deletar
      abrirModal({
        titulo: 'Opções da planilha',
        campos: [],
        onConfirm: () => {}
      });

      setTimeout(() => {
        if (!modalCampos || !modalForm) return;

        // Esconde os botões padrão (Salvar/Cancelar)
        const botoesFooter = modalForm.querySelector('.modal-botoes');
        if (botoesFooter) {
          botoesFooter.style.display = 'none';
        }

        // Insere as opções de ação no corpo do modal
        modalCampos.innerHTML = `
          <div class="modal-opcoes-planilha">
            <button type="button" class="modal-op-planilha modal-op-editar">
              <svg width="18" height="18"><use href="#edit" /></svg>
              <span>Editar planilha</span>
            </button>
            <button type="button" class="modal-op-planilha modal-op-deletar">
              <svg width="18" height="18"><use href="#delete" /></svg>
              <span>Deletar planilha</span>
            </button>
          </div>
        `;

        const btnOpcaoEditar = modalCampos.querySelector('.modal-op-editar');
        const btnOpcaoDeletar = modalCampos.querySelector('.modal-op-deletar');

        if (btnOpcaoEditar) {
          btnOpcaoEditar.onclick = () => {
            // Fecha o modal de opções e abre o modal de edição reaproveitando o handler existente
            fecharModal();
            setTimeout(() => {
              btnEdit.click();
            }, 220);
          };
        }

        if (btnOpcaoDeletar) {
          btnOpcaoDeletar.onclick = () => {
            // Fecha o modal de opções e abre o modal de deleção reaproveitando o handler existente
            fecharModal();
            setTimeout(() => {
              btnDel.click();
            }, 220);
          };
        }
      }, 15);
    };
    headerActions.appendChild(configBtn);
    div.appendChild(headerActions);
    listaPlanilhas.appendChild(div);
  });
}

// ========== MODAL DE ESCOLHA ==========
const modalChoiceBg = document.getElementById('modal-choice-bg');
const btnCriarCategoria = document.getElementById('btn-criar-categoria');
const btnCriarPlanilha = document.getElementById('btn-criar-planilha');
const modalChoiceClose = document.getElementById('modal-choice-close');

function abrirModalEscolha() {
  if (!modalChoiceBg) return;
  modalChoiceBg.style.display = 'flex';
  setTimeout(() => modalChoiceBg.classList.add('show'), 10);
}

function fecharModalEscolha() {
  if (!modalChoiceBg) return;
  modalChoiceBg.classList.remove('show');
  setTimeout(() => { modalChoiceBg.style.display = 'none'; }, 200);
}

// Conectar ao botão da sidebar
if (sidebarAddBtn) {
  sidebarAddBtn.onclick = abrirModalEscolha;
}

if (modalChoiceClose) {
  modalChoiceClose.onclick = fecharModalEscolha;
}

if (modalChoiceBg) {
  modalChoiceBg.onclick = (e) => { if (e.target === modalChoiceBg) fecharModalEscolha(); };
}

if (btnCriarCategoria) {
  btnCriarCategoria.onclick = async () => {
    fecharModalEscolha();
    abrirModal({
      titulo: 'Criar Categoria',
      campos: [
        { label: 'Nome da Categoria', name: 'nome', required: true, placeholder: 'Digite o nome...' }
      ],
      onConfirm: async (dados) => {
        if (dados.nome && dados.nome.trim()) {
          try {
            await criarCategoria(dados.nome.trim());
            atualizarCategorias();
            atualizarPlanilhas();
          } catch (e) {
            console.error(e);
          }
        }
      }
    });
  };
}

if (btnCriarPlanilha) {
  btnCriarPlanilha.onclick = async () => {
    fecharModalEscolha();
    const categorias = await carregarCategorias();
    abrirModal({
      titulo: 'Criar Planilha',
      campos: [
        { label: 'Nome da Planilha', name: 'titulo', required: true, placeholder: 'Digite o nome...' },
        { label: 'URL', name: 'url', required: true, type: 'url', placeholder: 'Cole a URL do Google Sheets' },
        {
          label: 'Imagem do card (URL ou /img/arquivo.png) - opcional',
          name: 'imagem',
          required: false,
          placeholder: 'Ex: https://... ou /img/minha-foto.png'
        },
        {
          label: 'Categoria', name: 'categoriaId', type: 'select', value: '',
          options: [{ value: '', label: 'Selecione' }].concat(categorias.map(c => ({ value: c.id, label: c.nome })))
        }
      ],
      onConfirm: async (dados) => {
        if (dados.titulo && dados.titulo.trim() && dados.url && dados.url.trim()) {
          try {
            await criarPlanilha(
              dados.titulo.trim(),
              dados.url.trim(),
              dados.categoriaId,
              dados.imagem
            );
            atualizarPlanilhas();
          } catch (e) {
            console.error(e);
          }
        }
      }
    });
  };
}

// Animação inicial
window.onload = () => {
  atualizarCategorias();
  atualizarPlanilhas();
};
