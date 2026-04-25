/**
 * Café Aroma — JavaScript principal
 * Utiliza apenas async/await para operações assíncronas (sem callbacks ou .then).
 *
 * Responsabilidades:
 *  1. Carregar produtos da API e renderizar os cards
 *  2. Gerenciar o carrinho de compras (adicionar, remover, ajustar quantidade)
 *  3. Enviar o pedido via POST /api/pedidos e exibir feedback ao usuário
 */

// ── Estado global da aplicação ─────────────────────────────────────────────
/** @type {Array<{id: number, nome: string, preco: number, quantidade: number}>} */
let carrinho = [];

/** @type {Array<Object>} Lista completa de produtos carregada da API */
let todosProdutos = [];

/** Categoria atualmente selecionada no filtro ('todos' = sem filtro) */
let categoriaAtiva = 'todos';

// ── Seletores do DOM ───────────────────────────────────────────────────────
const gridProdutos    = document.getElementById('grid-produtos');
const listaCarrinho   = document.getElementById('lista-carrinho');
const totalValor      = document.getElementById('total-valor');
const btnFinalizar    = document.getElementById('btn-finalizar');
const inputObservacao = document.getElementById('observacao');
const filtrosBtns     = document.querySelectorAll('.filtro-btn');
const toast           = document.getElementById('toast');

// ── Inicialização ──────────────────────────────────────────────────────────
/**
 * Ponto de entrada: executado quando o DOM estiver pronto.
 * Carrega os produtos da API e configura os listeners de eventos.
 */
document.addEventListener('DOMContentLoaded', async () => {
  await carregarProdutos();
  configurarFiltros();
  btnFinalizar.addEventListener('click', finalizarPedido);
});

// ── Funções de produto ─────────────────────────────────────────────────────

/**
 * Busca os produtos da API e renderiza o grid.
 * GET /api/produtos
 */
async function carregarProdutos() {
  try {
    gridProdutos.innerHTML = '<p style="color:#999">Carregando cardápio...</p>';
    const resposta = await fetch('/api/produtos');

    if (!resposta.ok) throw new Error(`Erro HTTP ${resposta.status}`);

    todosProdutos = await resposta.json();
    renderizarProdutos(todosProdutos);
  } catch (erro) {
    gridProdutos.innerHTML = '<p style="color:red">Falha ao carregar o cardápio. Tente novamente.</p>';
    console.error('Erro ao carregar produtos:', erro);
  }
}

/**
 * Renderiza os cards de produto no grid.
 * @param {Array<Object>} produtos - Lista de produtos a exibir
 */
function renderizarProdutos(produtos) {
  if (produtos.length === 0) {
    gridProdutos.innerHTML = '<p style="color:#999">Nenhum produto nesta categoria.</p>';
    return;
  }

  // Mapa de emojis por categoria para substituir imagens ausentes
  const emojiCategoria = {
    bebida:  '☕',
    salgado: '🥐',
    doce:    '🍰',
    outros:  '🛒'
  };

  gridProdutos.innerHTML = produtos.map(produto => {
    const emoji = emojiCategoria[produto.categoria] || '🛒';
    const precoFormatado = produto.preco.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    });

    return `
      <article class="produto-card" data-id="${produto.id}">
        <div class="produto-card__imagem">${emoji}</div>
        <div class="produto-card__corpo">
          <h3 class="produto-card__nome">${produto.nome}</h3>
          <p class="produto-card__descricao">${produto.descricao || ''}</p>
          <div class="produto-card__rodape">
            <span class="produto-card__preco">${precoFormatado}</span>
            <button
              class="btn-adicionar"
              onclick="adicionarAoCarrinho(${produto.id})"
              title="Adicionar ao carrinho"
              aria-label="Adicionar ${produto.nome} ao carrinho"
            >+</button>
          </div>
        </div>
      </article>
    `;
  }).join('');
}

// ── Funções de filtro ──────────────────────────────────────────────────────

/**
 * Configura os botões de filtro de categoria.
 * Ao clicar, filtra o grid de produtos pela categoria selecionada.
 */
function configurarFiltros() {
  filtrosBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filtrosBtns.forEach(b => b.classList.remove('ativo'));
      btn.classList.add('ativo');

      categoriaAtiva = btn.dataset.categoria;

      const filtrados = categoriaAtiva === 'todos'
        ? todosProdutos
        : todosProdutos.filter(p => p.categoria === categoriaAtiva);

      renderizarProdutos(filtrados);
    });
  });
}

// ── Funções do carrinho ────────────────────────────────────────────────────

/**
 * Adiciona um produto ao carrinho ou incrementa sua quantidade.
 * @param {number} produtoId - ID do produto a adicionar
 */
function adicionarAoCarrinho(produtoId) {
  const produto = todosProdutos.find(p => p.id === produtoId);
  if (!produto) return;

  const itemExistente = carrinho.find(i => i.id === produtoId);
  if (itemExistente) {
    itemExistente.quantidade += 1;
  } else {
    carrinho.push({
      id:         produto.id,
      nome:       produto.nome,
      preco:      produto.preco,
      quantidade: 1
    });
  }

  atualizarCarrinho();
  exibirToast(`"${produto.nome}" adicionado!`, 'sucesso');
}

/**
 * Altera a quantidade de um item no carrinho.
 * Se a quantidade chegar a 0, remove o item.
 * @param {number} produtoId  - ID do produto
 * @param {number} delta      - Variação (ex: +1 ou -1)
 */
function alterarQuantidade(produtoId, delta) {
  const item = carrinho.find(i => i.id === produtoId);
  if (!item) return;

  item.quantidade += delta;

  if (item.quantidade <= 0) {
    carrinho = carrinho.filter(i => i.id !== produtoId);
  }

  atualizarCarrinho();
}

/**
 * Atualiza a renderização do carrinho e recalcula o total.
 */
function atualizarCarrinho() {
  // Calcula o total
  const total = carrinho.reduce((soma, item) => soma + item.preco * item.quantidade, 0);
  totalValor.textContent = total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  // Habilita/desabilita botão finalizar
  btnFinalizar.disabled = carrinho.length === 0;

  // Renderiza lista do carrinho
  if (carrinho.length === 0) {
    listaCarrinho.innerHTML = '<p class="carrinho-vazio">☕ Seu carrinho está vazio</p>';
    return;
  }

  listaCarrinho.innerHTML = carrinho.map(item => {
    const subtotal = (item.preco * item.quantidade).toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    });
    return `
      <div class="carrinho-item">
        <span class="carrinho-item__nome">${item.nome}</span>
        <div class="carrinho-item__controles">
          <button class="btn-qtd" onclick="alterarQuantidade(${item.id}, -1)">−</button>
          <span class="carrinho-item__qtd">${item.quantidade}</span>
          <button class="btn-qtd" onclick="alterarQuantidade(${item.id}, +1)">+</button>
        </div>
        <span class="carrinho-item__subtotal">${subtotal}</span>
      </div>
    `;
  }).join('');
}

// ── Finalizar pedido ───────────────────────────────────────────────────────

/**
 * Envia o pedido para a API via POST /api/pedidos.
 * Usa async/await para aguardar a resposta do servidor.
 * Exibe feedback de sucesso (enquanto a impressora física emite o comprovante).
 */
async function finalizarPedido() {
  if (carrinho.length === 0) return;

  // Monta o payload do pedido
  const payload = {
    observacao: inputObservacao.value.trim(),
    itens: carrinho.map(item => ({
      produto_id: item.id,
      quantidade: item.quantidade
    }))
  };

  // Indica carregamento no botão
  btnFinalizar.disabled = true;
  btnFinalizar.innerHTML = '<span class="spinner"></span>Processando...';

  try {
    const resposta = await fetch('/api/pedidos', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload)
    });

    const dados = await resposta.json();

    if (resposta.ok) {
      // ✅ Sucesso: limpa o carrinho e exibe confirmação
      exibirToast(`✅ Pedido #${dados.pedido.id} confirmado! Imprimindo cupom...`, 'sucesso');
      carrinho = [];
      inputObservacao.value = '';
      atualizarCarrinho();
    } else {
      // ⚠️ Erro da API (400/404/500)
      exibirToast(`Erro: ${dados.erro || 'Falha ao enviar pedido.'}`, 'erro');
    }

  } catch (erro) {
    // ❌ Erro de rede ou servidor indisponível
    exibirToast('Erro de conexão. Verifique o servidor.', 'erro');
    console.error('Erro ao finalizar pedido:', erro);
  } finally {
    // Restaura o botão independente do resultado
    btnFinalizar.disabled = false;
    btnFinalizar.innerHTML = 'Finalizar Pedido';
  }
}

// ── Utilitários ────────────────────────────────────────────────────────────

/**
 * Exibe uma notificação (toast) temporária na tela.
 * @param {string} mensagem - Texto a exibir
 * @param {'sucesso'|'erro'} tipo - Cor do toast
 */
function exibirToast(mensagem, tipo = 'sucesso') {
  toast.textContent = mensagem;
  toast.className = `toast toast--${tipo} visivel`;

  // Remove o toast após 3.5 segundos
  setTimeout(() => {
    toast.classList.remove('visivel');
  }, 3500);
}
