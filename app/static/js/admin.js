/**
 * Café Aroma — admin.js
 * Painel de Gerenciamento de Produtos (CRUD completo).
 *
 * Operações:
 *   Create → POST   /api/produtos
 *   Read   → GET    /api/produtos/admin
 *   Update → PUT    /api/produtos/<id>
 *   Delete → DELETE /api/produtos/<id>
 *
 * Usa exclusivamente async/await para chamadas à API.
 */

// ── Estado do painel admin ─────────────────────────────────────────────────
/** @type {Array<Object>} Cache completo de produtos carregados */
let todosProdutosAdmin = [];

/** ID do produto selecionado para exclusão */
let idParaExcluir = null;

// ── Seletores do DOM ───────────────────────────────────────────────────────
const tabelaCorpo         = document.getElementById('tabela-corpo');
const btnNovoProduto      = document.getElementById('btn-novo-produto');
const modalOverlay        = document.getElementById('modal-overlay');
const modalFechar         = document.getElementById('modal-fechar');
const btnCancelar         = document.getElementById('btn-cancelar');
const formProduto         = document.getElementById('form-produto');
const modalTitulo         = document.getElementById('modal-titulo');
const btnSalvar           = document.getElementById('btn-salvar');
const formErro            = document.getElementById('form-erro');
const inputBusca          = document.getElementById('busca-produto');
const filtroStatus        = document.getElementById('filtro-status');
const modalExcluirOverlay = document.getElementById('modal-excluir-overlay');
const modalExcluirFechar  = document.getElementById('modal-excluir-fechar');
const btnExcluirCancelar  = document.getElementById('btn-excluir-cancelar');
const btnExcluirConfirmar = document.getElementById('btn-excluir-confirmar');
const msgExcluir          = document.getElementById('msg-excluir');

// Campos do formulário
const campoId          = document.getElementById('campo-id');
const campoNome        = document.getElementById('campo-nome');
const campoPreco       = document.getElementById('campo-preco');
const campoCategoria   = document.getElementById('campo-categoria');
const campoDescricao   = document.getElementById('campo-descricao');
const campoEstoque     = document.getElementById('campo-estoque');
const campoEstoqueMin  = document.getElementById('campo-estoque-min');
const campoAtivo       = document.getElementById('campo-ativo');

// ── Inicialização dos listeners ────────────────────────────────────────────
btnNovoProduto.addEventListener('click', abrirModalNovo);
modalFechar.addEventListener('click', fecharModal);
btnCancelar.addEventListener('click', fecharModal);
formProduto.addEventListener('submit', salvarProduto);
modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) fecharModal(); });

modalExcluirFechar.addEventListener('click', fecharModalExcluir);
btnExcluirCancelar.addEventListener('click', fecharModalExcluir);
btnExcluirConfirmar.addEventListener('click', confirmarExclusao);
modalExcluirOverlay.addEventListener('click', e => { if (e.target === modalExcluirOverlay) fecharModalExcluir(); });

inputBusca.addEventListener('input', filtrarTabela);
filtroStatus.addEventListener('change', filtrarTabela);

// ── READ — Carregar tabela ─────────────────────────────────────────────────

/**
 * Busca todos os produtos (inclusive inativos) e renderiza a tabela.
 * GET /api/produtos/admin
 */
async function carregarTabelaProdutos() {
  tabelaCorpo.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#999;padding:2rem">
    <span class="spinner" style="border-color:rgba(0,0,0,.2);border-top-color:#795548"></span>
    Carregando produtos...
  </td></tr>`;

  try {
    const resposta = await fetch('/api/produtos/admin');
    if (!resposta.ok) throw new Error(`Erro HTTP ${resposta.status}`);

    todosProdutosAdmin = await resposta.json();
    renderizarTabela(todosProdutosAdmin);
  } catch (erro) {
    tabelaCorpo.innerHTML = `<tr><td colspan="7" style="text-align:center;color:red;padding:2rem">
      Falha ao carregar produtos. Verifique a conexão com o servidor.
    </td></tr>`;
    console.error('Erro ao carregar produtos admin:', erro);
  }
}

/**
 * Renderiza as linhas da tabela com os produtos fornecidos.
 * @param {Array<Object>} produtos
 */
function renderizarTabela(produtos) {
  if (produtos.length === 0) {
    tabelaCorpo.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#999;padding:2rem">
      Nenhum produto encontrado.
    </td></tr>`;
    return;
  }

  const emojiCategoria = { bebida: '☕', salgado: '🥐', doce: '🍰', outros: '🛒' };

  tabelaCorpo.innerHTML = produtos.map(p => {
    const precoFmt = parseFloat(p.preco).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    const emoji    = emojiCategoria[p.categoria] || '🛒';
    const estoqueFmt = p.estoque_quantidade ?? 0;
    const classEstoque = p.estoque_baixo ? 'estoque-baixo' : '';
    const badgeAtivo = p.ativo
      ? '<span class="badge badge--ativo">✔ Ativo</span>'
      : '<span class="badge badge--inativo">✖ Inativo</span>';
    const btnAtivo = p.ativo
      ? `<button class="btn-acao btn-acao--excluir" onclick="confirmarDesativar(${p.id}, '${escaparHtml(p.nome)}')">🔴 Desativar</button>`
      : `<button class="btn-acao btn-acao--ativar" onclick="ativarProduto(${p.id}, '${escaparHtml(p.nome)}')">🟢 Ativar</button>`;

    return `
      <tr>
        <td style="color:#999; font-size:0.8rem">#${p.id}</td>
        <td>
          <strong>${escaparHtml(p.nome)}</strong>
          ${p.descricao ? `<br><small style="color:#999">${escaparHtml(p.descricao)}</small>` : ''}
        </td>
        <td>${emoji} ${p.categoria ?? '—'}</td>
        <td><strong>${precoFmt}</strong></td>
        <td class="${classEstoque}" title="Mínimo: ${p.estoque_minimo ?? 5}">
          ${estoqueFmt} un.
          ${p.estoque_baixo ? ' ⚠️' : ''}
        </td>
        <td>${badgeAtivo}</td>
        <td>
          <div class="acoes-tabela">
            <button class="btn-acao btn-acao--editar" onclick="abrirModalEdicao(${p.id})">✏️ Editar</button>
            ${btnAtivo}
            <button class="btn-acao btn-acao--excluir" onclick="confirmarExclusaoPermanente(${p.id}, '${escaparHtml(p.nome)}')">🗑️</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

/** Filtra a tabela em tempo real pela busca e filtro de status. */
function filtrarTabela() {
  const termo  = inputBusca.value.toLowerCase().trim();
  const status = filtroStatus.value;

  const filtrados = todosProdutosAdmin.filter(p => {
    const textoMatch = p.nome.toLowerCase().includes(termo) ||
                       (p.categoria ?? '').toLowerCase().includes(termo) ||
                       (p.descricao ?? '').toLowerCase().includes(termo);
    const statusMatch = status === 'todos' ||
                        (status === 'ativo' && p.ativo) ||
                        (status === 'inativo' && !p.ativo);
    return textoMatch && statusMatch;
  });

  renderizarTabela(filtrados);
}

// ── CREATE — Novo produto ──────────────────────────────────────────────────

/** Abre o modal em modo de criação (campos zerados). */
function abrirModalNovo() {
  campoId.value        = '';
  campoNome.value      = '';
  campoPreco.value     = '';
  campoCategoria.value = 'bebida';
  campoDescricao.value = '';
  campoEstoque.value   = '0';
  campoEstoqueMin.value = '5';
  campoAtivo.checked   = true;
  modalTitulo.textContent = 'Novo Produto';
  esconderErroForm();
  modalOverlay.classList.remove('oculto');
  campoNome.focus();
}

// ── UPDATE — Editar produto ────────────────────────────────────────────────

/**
 * Abre o modal pré-preenchido com os dados do produto para edição.
 * @param {number} id - ID do produto
 */
async function abrirModalEdicao(id) {
  const produto = todosProdutosAdmin.find(p => p.id === id);
  if (!produto) return;

  campoId.value          = produto.id;
  campoNome.value        = produto.nome;
  campoPreco.value       = produto.preco;
  campoCategoria.value   = produto.categoria || 'outros';
  campoDescricao.value   = produto.descricao || '';
  campoEstoque.value     = produto.estoque_quantidade ?? 0;
  campoEstoqueMin.value  = produto.estoque_minimo ?? 5;
  campoAtivo.checked     = produto.ativo;
  modalTitulo.textContent = `Editar: ${produto.nome}`;
  esconderErroForm();
  modalOverlay.classList.remove('oculto');
  campoNome.focus();
}

// ── SAVE — Submissão do formulário (Create ou Update) ─────────────────────

/**
 * Intercepta o submit do formulário.
 * Se houver ID → PUT (atualizar). Caso contrário → POST (criar).
 * @param {Event} evento
 */
async function salvarProduto(evento) {
  evento.preventDefault();
  esconderErroForm();

  const nome  = campoNome.value.trim();
  const preco = parseFloat(campoPreco.value);

  if (!nome) return exibirErroForm('O nome do produto é obrigatório.');
  if (isNaN(preco) || preco < 0) return exibirErroForm('Informe um preço válido (maior ou igual a 0).');

  const payload = {
    nome,
    preco,
    categoria:          campoCategoria.value,
    descricao:          campoDescricao.value.trim(),
    ativo:              campoAtivo.checked,
    estoque_quantidade: parseInt(campoEstoque.value) || 0,
    estoque_minimo:     parseInt(campoEstoqueMin.value) || 5,
    estoque_inicial:    parseInt(campoEstoque.value) || 0,
  };

  const id = campoId.value;
  const url    = id ? `/api/produtos/${id}` : '/api/produtos';
  const metodo = id ? 'PUT' : 'POST';

  btnSalvar.disabled = true;
  btnSalvar.innerHTML = '<span class="spinner"></span>Salvando...';

  try {
    const resposta = await fetch(url, {
      method:  metodo,
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload)
    });

    const dados = await resposta.json();

    if (resposta.ok) {
      fecharModal();
      await carregarTabelaProdutos();
      // Recarrega o cardápio do PDV também
      await carregarProdutos();
      exibirToast(id ? `✅ "${nome}" atualizado!` : `✅ "${nome}" cadastrado!`, 'sucesso');
    } else {
      exibirErroForm(dados.erro || 'Erro ao salvar produto.');
    }
  } catch (erro) {
    exibirErroForm('Erro de conexão com o servidor.');
    console.error('Erro ao salvar produto:', erro);
  } finally {
    btnSalvar.disabled = false;
    btnSalvar.innerHTML = '💾 Salvar Produto';
  }
}

// ── DELETE — Exclusão e desativação ───────────────────────────────────────

/**
 * Abre o modal de confirmação para exclusão permanente.
 * @param {number} id
 * @param {string} nome
 */
function confirmarExclusaoPermanente(id, nome) {
  idParaExcluir = id;
  msgExcluir.innerHTML = `Deseja <strong>remover permanentemente</strong> o produto:<br>
    <strong>"${nome}"</strong>?<br><br>
    <small style="color:#999">⚠️ Se houver pedidos vinculados, o produto será <u>desativado</u> em vez de removido para preservar o histórico.</small>`;
  modalExcluirOverlay.classList.remove('oculto');
}

/**
 * Abre o modal de confirmação para desativar (soft delete) um produto ativo.
 * @param {number} id
 * @param {string} nome
 */
function confirmarDesativar(id, nome) {
  idParaExcluir = id;
  msgExcluir.innerHTML = `Deseja <strong>desativar</strong> o produto:<br>
    <strong>"${nome}"</strong>?<br><br>
    <small style="color:#999">O produto ficará invisível no cardápio, mas seu histórico de vendas será preservado. Você pode reativá-lo a qualquer momento.</small>`;
  modalExcluirOverlay.classList.remove('oculto');
}

/**
 * Confirma a exclusão/desativação chamando DELETE /api/produtos/<id>.
 */
async function confirmarExclusao() {
  if (!idParaExcluir) return;

  btnExcluirConfirmar.disabled = true;
  btnExcluirConfirmar.textContent = 'Removendo...';

  try {
    const resposta = await fetch(`/api/produtos/${idParaExcluir}`, { method: 'DELETE' });
    const dados = await resposta.json();

    if (resposta.ok) {
      fecharModalExcluir();
      await carregarTabelaProdutos();
      await carregarProdutos();
      exibirToast(dados.mensagem, 'sucesso');
    } else {
      fecharModalExcluir();
      exibirToast(dados.erro || 'Erro ao remover produto.', 'erro');
    }
  } catch (erro) {
    fecharModalExcluir();
    exibirToast('Erro de conexão com o servidor.', 'erro');
    console.error('Erro ao excluir produto:', erro);
  } finally {
    btnExcluirConfirmar.disabled = false;
    btnExcluirConfirmar.innerHTML = '🗑️ Confirmar Exclusão';
    idParaExcluir = null;
  }
}

/**
 * Reativa um produto inativo via PUT /api/produtos/<id> com ativo=true.
 * @param {number} id
 * @param {string} nome
 */
async function ativarProduto(id, nome) {
  try {
    const resposta = await fetch(`/api/produtos/${id}`, {
      method:  'PUT',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ ativo: true })
    });

    if (resposta.ok) {
      await carregarTabelaProdutos();
      await carregarProdutos();
      exibirToast(`✅ "${nome}" reativado no cardápio!`, 'sucesso');
    } else {
      exibirToast('Erro ao reativar produto.', 'erro');
    }
  } catch (erro) {
    exibirToast('Erro de conexão com o servidor.', 'erro');
  }
}

// ── Utilitários do modal ───────────────────────────────────────────────────

function fecharModal() {
  modalOverlay.classList.add('oculto');
  formProduto.reset();
  esconderErroForm();
}

function fecharModalExcluir() {
  modalExcluirOverlay.classList.add('oculto');
  idParaExcluir = null;
}

function exibirErroForm(msg) {
  formErro.textContent = msg;
  formErro.classList.remove('oculto');
}

function esconderErroForm() {
  formErro.textContent = '';
  formErro.classList.add('oculto');
}

/** Escapa caracteres HTML para evitar XSS na montagem de innerHTML. */
function escaparHtml(texto) {
  return String(texto)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// Fecha modais com ESC
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    fecharModal();
    fecharModalExcluir();
  }
});
