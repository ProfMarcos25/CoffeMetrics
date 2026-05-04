# ☕ Café Aroma — Sistema de Pedidos Inteligente

> **Versão:** 2.2 · **Atualizado em:** Maio/2026

Projeto pedagógico desenvolvido para alunos de Técnico em **Ciência de Dados** e **Desenvolvimento de Sistemas** (1º ano). Une um PDV funcional (Front-end), motor de IA preditiva (Back-end), gerenciamento completo de produtos com CRUD e automação de hardware (Impressão Térmica ESC/POS).

---

## 📋 Índice

1. [Funcionalidades](#-funcionalidades)
2. [Stack Tecnológica](#-stack-tecnológica)
3. [Estrutura de Pastas](#-estrutura-de-pastas)
4. [Instalação e Execução](#-instalação-e-execução)
5. [Banco de Dados](#-banco-de-dados)
6. [Rotas da API](#-rotas-da-api)
7. [Painel de Gerenciamento CRUD](#-painel-de-gerenciamento-crud)
8. [Impressora Térmica](#-impressora-térmica)
9. [Módulo de IA — Analytics](#-módulo-de-ia--analytics)
10. [Dados de Exemplo](#-dados-de-exemplo-seedpy)

---

## ✨ Funcionalidades

### 🛒 PDV — Ponto de Venda
- Cardápio dinâmico carregado da API com cards visuais por categoria
- Filtros rápidos: **Todos · Bebidas · Salgados · Doces**
- Carrinho de compras com controle de quantidade (+/−)
- Campo de observações por pedido
- Botão **Finalizar Pedido** — grava no banco e imprime cupom automaticamente
- Feedback em tempo real com notificações toast
- Relógio ao vivo no cabeçalho

### ⚙️ Painel de Gerenciamento de Produtos (CRUD completo)
- Tabela com todos os produtos (ativos e inativos) + dados de estoque
- **Busca em tempo real** por nome, categoria ou descrição
- **Filtro** por status: Ativo / Inativo / Todos
- **Criar** produto via modal com validação de campos
- **Editar** produto — modal pré-preenchido com todos os dados atuais
- **Desativar / Reativar** produto sem perder histórico de vendas
- **Excluir** produto com confirmação — soft delete automático se houver pedidos vinculados
- Indicador visual de **⚠️ Estoque Baixo** quando abaixo do mínimo configurado

### 🧠 Analytics (IA)
- Previsão de demanda por produto com **Regressão Linear** (scikit-learn)
- Ranking dos produtos mais vendidos

### 📲 Notificações via Telegram
- A cada pedido finalizado, uma mensagem formatada é enviada automaticamente ao bot configurado
- Envia em thread separada (não bloqueia a resposta da API)
- Fallback: se o token/chat_id não estiver configurado, o pedido prossegue normalmente

### 🖨️ Impressão Térmica
- Cupom ESC/POS na **LUOGAO VS-5890C** (58mm / 32 colunas)
- QR Code com o ID do pedido
- Fallback: se a impressora estiver offline, o pedido prossegue normalmente

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Front-end | HTML5 · CSS3 (variáveis CSS) · JavaScript ES6+ (async/await) | — |
| Back-end | Python + Flask | 3.10+ / 3.0.3 |
| ORM | Flask-SQLAlchemy | 3.1.1 |
| Banco de Dados | PostgreSQL | 14+ |
| Driver DB | psycopg2-binary | 2.9.9 |
| Hardware | python-escpos (ESC/POS) | 3.1 |
| IA / ML | scikit-learn · numpy · pandas | 1.5.0 |
| QR Code | qrcode | 8.2 |
| Notificações | requests (Telegram Bot API) | 2.31+ |
| Configuração | python-dotenv | 1.0+

---

## 📁 Estrutura de Pastas

```
CAFEAROMA/
├── run.py                          ← Ponto de entrada (inicia o Flask)
├── seed.py                         ← Popula o banco com produtos de exemplo
├── requirements.txt                ← Dependências Python
├── README.md
├── .env                            ← Variáveis de ambiente reais (não versionar!)
├── .env.example                    ← Modelo de variáveis de ambiente
│
├── data/
│   ├── config.json                 ← Configurações de fallback (impressora, etc.)
│   └── schema.sql                  ← Script DDL do PostgreSQL
│
└── app/
    ├── __init__.py                 ← Application Factory: carrega .env → config.json
    │
    ├── models/
    │   └── models.py               ← ORM: Usuario, Produto, Pedido, ItemPedido, Estoque
    │
    ├── controllers/
    │   ├── pedidos_controller.py   ← GET/POST /api/pedidos + notificação Telegram
    │   ├── produtos_controller.py  ← CRUD completo /api/produtos
    │   └── analytics_controller.py ← /api/analytics/...
    │
    ├── services/
    │   ├── printer_service.py      ← Impressão ESC/POS → LUOGAO VS-5890C (thread)
    │   ├── telegram_service.py     ← Notificações via Telegram Bot API (thread)
    │   └── analytics.py            ← Regressão Linear (scikit-learn)
    │
    ├── static/
    │   ├── css/style.css           ← Design marrom/bege, variáveis CSS, responsivo
    │   └── js/
    │       ├── main.js             ← PDV: cardápio, carrinho, finalizar pedido
    │       └── admin.js            ← CRUD de produtos: tabela, modal, busca
    │
    └── templates/
        └── index.html              ← SPA com duas abas: PDV e Gerenciamento
```

---

## 🚀 Instalação e Execução

### 1. Pré-requisitos

| Software | Observação |
|----------|-----------|
| Python 3.10+ | `py --version` |
| PostgreSQL 14+ | Servidor rodando localmente |
| LUOGAO VS-5890C | **Opcional** — impressão desativada se offline |



### 1.1 Virtualizar Python

```powershell
py -m venv .venv
```

### 1.2 Ativar no Ambiente Windows

```powershell
.venv\Scripts\activate
```


```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& c:SEU_DIRETORIO_AQUI\projetos\IAMetrics\.venv\Scripts\Activate.ps1)
```

### 1.3 comfigurar biblioteca 

-- Baixar o arquivo do site libusb
https://github.com/libusb/libusb/releases


Instale a biblioteca no seu ambiente virtual:
Com o terminal aberto e o seu .venv ativado, rode:

```Bash
pip install pyusb
```

Instale o "motor" (libusb-1.0.dll):
O Python não consegue falar com o USB sozinho no Windows. Você precisa desse arquivo:


Baixe o arquivo libusb-1.0.27.7z (ou a versão mais recente) no site oficial do libusb.

Abra a pasta VS2015-x64/dll dentro do arquivo baixado.

Copie o arquivo libusb-1.0.dll.

Cole esse arquivo dentro da pasta Scripts do seu ambiente virtual: .venv\Scripts\ (onde está o seu python.exe).

Configuração de Driver (Zadig):
Se mesmo assim não funcionar, o Windows está protegendo o driver original da impressora.

Baixe o Zadig.

Vá em Options > List All Devices.

Selecione sua impressora LUOGAO na lista.

Mude o driver para WinUSB ou libusb-win32 e clique em Replace Driver.

Aviso: Isso fará com que a impressora pare de aparecer como uma impressora comum no Windows e passe a ser um "Dispositivo USB Genérico" que só o seu script Python conseguirá controlar.


### 2. Instalar dependências

```powershell
py -m pip install -r requirements.txt
```

### 3. Criar o banco de dados

```powershell
# Cria o banco
psql -U postgres -c "CREATE DATABASE cafearoma;"

# Cria as tabelas
psql -U postgres -d cafearoma -f data/schema.sql
```

### 4. Configurar variáveis de ambiente

Copie o arquivo modelo e preencha com seus dados:

```powershell
copy .env.example .env
```

Edite o `.env` com seus valores reais:

```dotenv
# =============================================================
# Variáveis de ambiente do projeto Café Aroma — ARQUIVO REAL
# NÃO envie este arquivo para o repositório!
# Ele já deve estar listado no .gitignore
# =============================================================

# ── Flask ──────────────────────────────────────────────────────
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=cafearoma-secret-key-2026

# ── PostgreSQL ─────────────────────────────────────────────────
DATABASE_URI=postgresql://postgres:6$o#fJ@localhost:5432/cafearoma

# ── Telegram Bot ───────────────────────────────────────────────
# 1. Crie um bot com @BotFather no Telegram e cole o token abaixo
# 2. Envie uma mensagem ao bot e acesse:
#    https://api.telegram.org/bot<TOKEN>/getUpdates
#    para obter o CHAT_ID (pode ser negativo para grupos)
TELEGRAM_BOT_TOKEN=8756218296:AAGjYY8tCs0rmFY0d_4dNsixZxWIL-ffIwQ
TELEGRAM_CHAT_ID=634033523

# ── Impressora Térmica ─────────────────────────────────────────
PRINTER_INTERFACE=USB
PRINTER_VENDOR_ID=0x0416
PRINTER_PRODUCT_ID=0x5011
# Usado apenas quando PRINTER_INTERFACE=NETWORK:
# PRINTER_HOST=192.168.1.100
# PRINTER_PORT=9100

```

> **Prioridade de configuração:** variáveis do `.env` sempre sobrescrevem `data/config.json`.
> O `config.json` serve apenas como fallback para quem preferir não usar `.env`.

> ⚠️ **Nunca versione o arquivo `.env`** — ele já está no `.gitignore`.

### 5. (Opcional) Popular o banco com produtos de exemplo

```powershell
py seed.py
```

> O seed é seguro para rodar múltiplas vezes — verifica duplicatas automaticamente.
> Alternativamente, cadastre os produtos diretamente pela aba **⚙️ Gerenciar Produtos** na interface.

### 6. Iniciar o servidor

```powershell
py run.py
```

Acesse: **http://localhost:5000**

---

## 🗄️ Banco de Dados

### Tabelas

| Tabela | Descrição |
|--------|-----------|
| `usuarios` | Clientes e operadores do sistema |
| `produtos` | Catálogo do cardápio (com flag `ativo`) |
| `pedidos` | Registro de cada venda |
| `itens_pedido` | Produtos dentro de cada pedido |
| `estoque` | Quantidade disponível por produto |

### Diagrama simplificado

```
usuarios ──< pedidos ──< itens_pedido >── produtos ──── estoque
```

---

## 📡 Rotas da API

### Produtos

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/produtos` | Lista produtos **ativos** (cardápio do PDV) |
| `GET` | `/api/produtos/admin` | Lista **todos** os produtos + estoque (painel admin) |
| `GET` | `/api/produtos/<id>` | Detalha um produto |
| `POST` | `/api/produtos` | **Cria** novo produto com estoque |
| `PUT` | `/api/produtos/<id>` | **Atualiza** dados e/ou estoque |
| `DELETE` | `/api/produtos/<id>` | **Remove** (ou desativa se tiver pedidos vinculados) |

### Pedidos

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/pedidos` | Cria pedido → grava no banco + impressão térmica + notificação Telegram |
| `GET` | `/api/pedidos` | Lista todos os pedidos |
| `GET` | `/api/pedidos/<id>` | Detalha um pedido |

### Analytics

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/analytics/mais-vendidos?top=5` | Ranking de produtos mais vendidos |
| `GET` | `/api/analytics/previsao/<produto_id>` | Previsão de demanda (Regressão Linear) |

### Exemplo — `POST /api/pedidos`

```json
{
  "observacao": "Sem açúcar",
  "itens": [
    { "produto_id": 1, "quantidade": 2 },
    { "produto_id": 7, "quantidade": 3 }
  ]
}
```

---

## ⚙️ Painel de Gerenciamento (CRUD)

Acessível pela aba **⚙️ Gerenciar Produtos** na interface principal.

### Ações disponíveis

| Ação | Comportamento |
|------|--------------|
| **+ Novo Produto** | Abre modal com formulário em branco |
| **✏️ Editar** | Abre modal pré-preenchido com os dados atuais |
| **🔴 Desativar** | Oculta o produto do cardápio (mantém histórico) |
| **🟢 Ativar** | Recoloca o produto no cardápio |
| **🗑️ Excluir** | Pede confirmação; faz soft delete se houver pedidos vinculados |

### Campos do formulário

| Campo | Tipo | Obrigatório |
|-------|------|:-----------:|
| Nome | Texto (max 100) | ✔ |
| Preço | Número decimal | ✔ |
| Categoria | bebida / salgado / doce / outros | — |
| Descrição | Texto | — |
| Estoque atual | Inteiro ≥ 0 | — |
| Estoque mínimo | Inteiro ≥ 0 (gera alerta ⚠️) | — |
| Ativo | Checkbox (visível no cardápio) | — |

---

## 📲 Notificações via Telegram Bot

A cada pedido finalizado, o `telegram_service.py` envia uma mensagem formatada em HTML para um chat ou grupo do Telegram.

### Como configurar

1. Abra o Telegram e converse com **@BotFather**
2. Digite `/newbot` e siga as instruções para obter o **token**
3. Envie uma mensagem ao bot, depois acesse:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
   para obter o **chat_id** (pode ser negativo para grupos)
4. Preencha no `.env`:
   ```dotenv
   TELEGRAM_BOT_TOKEN=8756218296:AAGjYY8tCs0rmFY0d_4dNsixZxWIL-ffIwQ
   TELEGRAM_CHAT_ID=634033523
   ```
 5. Obtenha o Id no `link`:
   ```dotenv
   https://api.telegram.org/bot8756218296:AAGjYY8tCs0rmFY0d_4dNsixZxWIL-ffIwQ/getUpdates
   ```
   

### Exemplo de mensagem enviada

```
☕ Novo Pedido — Café Aroma

🔢 Pedido Nº: 42
📅 25/04/2026 14:30

📋 Itens:
  • Café Expresso x2 — R$ 11,00
  • Pão de Queijo x3 — R$ 13,50

💰 Total: R$ 24,50
📝 Obs: Sem açúcar
```

> **Fallback:** se `TELEGRAM_BOT_TOKEN` ou `TELEGRAM_CHAT_ID` não estiverem configurados, o pedido é processado normalmente sem enviar a notificação.

---

## 🖨️ Impressora Térmica

- **Modelo:** LUOGAO VS-5890C (papel 58mm)
- **Protocolo:** ESC/POS via `python-escpos`
- **Interface:** USB (padrão) ou Network (configurável em `config.json`)
- **Largura:** máximo **32 caracteres** por linha

### Layout do Cupom

```
================================
         CAFÉ AROMA
       Cafeteria Inteligente
--------------------------------
Data: 25/04/2026 14:30
Pedido Nº: 42
--------------------------------
ITENS
Café Expresso x2     R$  11,00
Pão de Queijo x3     R$  13,50
--------------------------------
               TOTAL: R$ 24,50
--------------------------------
    [QR CODE — ID do pedido]

      Obrigado pela visita!
         Volte sempre :)
================================
```

### Principais comandos ESC/POS utilizados

| Comando | Função |
|---------|--------|
| `ESC a 1` | Centraliza texto |
| `ESC E 1` | Ativa negrito |
| `GS ( k` | Gera QR Code |
| `ESC d n` | Avança n linhas |
| `GS V 0` | Corte do papel |

> **Fallback:** se a impressora estiver offline, o erro é registrado no log e o pedido prossegue normalmente no banco e na fila.

---

## 🧠 Módulo de IA — Analytics

Utiliza **Regressão Linear** do `scikit-learn` para prever a demanda futura com base no histórico de vendas diárias.

**Fórmula:**
```
y = β₀ + β₁·x
x = período (dia/semana)   y = quantidade prevista
```

### Resposta do endpoint `/api/analytics/previsao/<id>`

```json
{
  "produto": "Café Expresso",
  "produto_id": 1,
  "previsao_proximo_periodo": 28.5,
  "coeficiente_angular": 1.2,
  "intercepto": 18.1,
  "r2_score": 0.94,
  "erro": null
}
```

| Campo | Significado |
|-------|------------|
| `previsao_proximo_periodo` | Quantidade estimada para o próximo período |
| `coeficiente_angular` | Taxa de crescimento (+) ou queda (−) por período |
| `r2_score` | Precisão: 1.0 = perfeito · 0.0 = sem correlação |

---

## 🌱 Dados de Exemplo (seed.py)

O `seed.py` insere **12 produtos** e **1 usuário operador** no banco, com verificação de duplicatas.

```powershell
py seed.py
```

**Saída esperada:**
```
🌱 Populando banco de dados...

✅ Seed concluído!
   • Produtos inseridos : 12
   • Produtos ignorados : 0
   • Operador criado    : Sim
```

| Categoria | Produtos |
|-----------|---------|
| ☕ Bebidas | Café Expresso, Cappuccino, Latte, Café com Leite, Chocolate Quente, Suco de Laranja |
| 🥐 Salgados | Pão de Queijo, Coxinha, Croissant |
| 🍰 Doces | Bolo de Cenoura, Fatia de Cheesecake, Brigadeiro |

---

## 📐 Padrões de Código

- **Python:** docstrings em português, comentários explicativos sobre ESC/POS e Telegram Bot API
- **JavaScript:** exclusivamente `async/await` (sem `.then()` ou callbacks)
- **CSS:** variáveis custom (`--cafe-escuro`, `--cafe-bege`, etc.), design responsivo
- **Flask:** padrão *Application Factory* + *Blueprints* por domínio
- **Erros:** todos os serviços externos (impressora, fila) tratam exceções sem derrubar o sistema