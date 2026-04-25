-- ============================================================
-- Script SQL — Café Aroma
-- Cria o banco de dados e as tabelas no PostgreSQL
-- Execute: psql -U postgres -f data/schema.sql
-- ============================================================

-- Cria o banco (rodar separado se necessário)
-- CREATE DATABASE cafearoma;

\c cafearoma;

-- ── Tabela: usuarios ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(100)  NOT NULL,
    email       VARCHAR(150)  NOT NULL UNIQUE,
    senha_hash  VARCHAR(256)  NOT NULL,
    perfil      VARCHAR(20)   DEFAULT 'cliente',
    criado_em   TIMESTAMP     DEFAULT NOW()
);

-- ── Tabela: produtos ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS produtos (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(100)  NOT NULL,
    descricao   TEXT,
    preco       NUMERIC(10,2) NOT NULL,
    categoria   VARCHAR(50),
    ativo       BOOLEAN       DEFAULT TRUE,
    imagem_url  VARCHAR(255),
    criado_em   TIMESTAMP     DEFAULT NOW()
);

-- ── Tabela: pedidos ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pedidos (
    id          SERIAL PRIMARY KEY,
    usuario_id  INTEGER       REFERENCES usuarios(id) ON DELETE SET NULL,
    status      VARCHAR(30)   DEFAULT 'pendente',
    total       NUMERIC(10,2) NOT NULL DEFAULT 0,
    observacao  TEXT,
    criado_em   TIMESTAMP     DEFAULT NOW()
);

-- ── Tabela: itens_pedido ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS itens_pedido (
    id              SERIAL PRIMARY KEY,
    pedido_id       INTEGER       NOT NULL REFERENCES pedidos(id)  ON DELETE CASCADE,
    produto_id      INTEGER       NOT NULL REFERENCES produtos(id) ON DELETE RESTRICT,
    quantidade      INTEGER       NOT NULL DEFAULT 1,
    preco_unitario  NUMERIC(10,2) NOT NULL
);

-- ── Tabela: estoque ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS estoque (
    id                 SERIAL PRIMARY KEY,
    produto_id         INTEGER NOT NULL UNIQUE REFERENCES produtos(id) ON DELETE CASCADE,
    quantidade         INTEGER NOT NULL DEFAULT 0,
    quantidade_minima  INTEGER DEFAULT 5,
    atualizado_em      TIMESTAMP DEFAULT NOW()
);

-- ── Índices para performance ─────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_pedidos_criado_em   ON pedidos(criado_em DESC);
CREATE INDEX IF NOT EXISTS idx_itens_pedido_id     ON itens_pedido(pedido_id);
CREATE INDEX IF NOT EXISTS idx_itens_produto_id    ON itens_pedido(produto_id);
CREATE INDEX IF NOT EXISTS idx_produtos_categoria  ON produtos(categoria);
