-- ============================================================
-- DROP TABLES (somente para recriar toda a estrutura do zero)
-- ============================================================
DROP TABLE IF EXISTS public.itens_pedido CASCADE;
DROP TABLE IF EXISTS public.pedidos CASCADE;
DROP TABLE IF EXISTS public.produtos CASCADE;
DROP TABLE IF EXISTS public.clientes CASCADE;

-- ============================================================
-- TABELA CLIENTES
-- ============================================================
CREATE TABLE IF NOT EXISTS public.clientes (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nome TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  telefone TEXT,
  criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- ============================================================
-- TABELA PRODUTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.produtos (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nome TEXT NOT NULL,
  preco NUMERIC NOT NULL CHECK (preco >= 0),
  quantidade INTEGER NOT NULL CHECK (quantidade >= 0),
  categoria TEXT,
  criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- TABELA PEDIDOS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.pedidos (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  cliente_id BIGINT NOT NULL REFERENCES public.clientes(id) ON DELETE CASCADE,
  total NUMERIC DEFAULT 0,
  status TEXT DEFAULT 'pendente',
  criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- TABELA ITENS_PEDIDO
-- ============================================================
CREATE TABLE IF NOT EXISTS public.itens_pedido (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  pedido_id BIGINT NOT NULL REFERENCES public.pedidos(id) ON DELETE CASCADE,
  produto_id BIGINT NOT NULL REFERENCES public.produtos(id) ON DELETE CASCADE,
  quantidade INTEGER NOT NULL CHECK (quantidade > 0),
  preco_unitario NUMERIC NOT NULL CHECK (preco_unitario >= 0)
);

-- ============================================================
-- FUNÇÃO PARA RE-CALCULAR TOTAL DO PEDIDO
-- ============================================================
CREATE OR REPLACE FUNCTION public.fn_recalcular_total_pedido(p_pedido_id bigint)
RETURNS void
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
  UPDATE public.pedidos
  SET total = COALESCE((
    SELECT SUM(quantidade * preco_unitario)
    FROM public.itens_pedido
    WHERE pedido_id = p_pedido_id
  ), 0)
  WHERE id = p_pedido_id;
END;
$$;

-- ============================================================
-- TRIGGER PARA RE-CALCULAR TOTAL
-- ============================================================
CREATE OR REPLACE FUNCTION public.trg_atualizar_total_pedido()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE
  affected_pedido bigint;
BEGIN
  IF TG_OP = 'INSERT' THEN
    affected_pedido := NEW.pedido_id;
  ELSIF TG_OP = 'UPDATE' THEN
    IF NEW.pedido_id IS DISTINCT FROM OLD.pedido_id THEN
      PERFORM public.fn_recalcular_total_pedido(OLD.pedido_id);
    END IF;
    affected_pedido := NEW.pedido_id;
  ELSIF TG_OP = 'DELETE' THEN
    affected_pedido := OLD.pedido_id;
  END IF;

  PERFORM public.fn_recalcular_total_pedido(affected_pedido);

  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  ELSE
    RETURN NEW;
  END IF;
END;
$$;

DROP TRIGGER IF EXISTS tr_itens_pedido_after_change ON public.itens_pedido;

CREATE TRIGGER tr_itens_pedido_after_change
AFTER INSERT OR UPDATE OR DELETE ON public.itens_pedido
FOR EACH ROW
EXECUTE PROCEDURE public.trg_atualizar_total_pedido();

-- ============================================================
-- FUNÇÃO PARA CONTROLE AUTOMÁTICO DE ESTOQUE
-- ============================================================
CREATE OR REPLACE FUNCTION public.fn_atualizar_estoque()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE
  estoque_atual INT;
  diferenca INT;
BEGIN
  IF TG_OP = 'INSERT' THEN
    SELECT quantidade INTO estoque_atual FROM public.produtos WHERE id = NEW.produto_id;
    IF estoque_atual IS NULL THEN
      RAISE EXCEPTION 'Produto não encontrado para atualização de estoque.';
    END IF;
    IF estoque_atual < NEW.quantidade THEN
      RAISE EXCEPTION 'Estoque insuficiente para este produto.';
    END IF;
    UPDATE public.produtos SET quantidade = quantidade - NEW.quantidade WHERE id = NEW.produto_id;
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    IF NEW.produto_id <> OLD.produto_id THEN
      -- devolve o estoque do produto antigo
      UPDATE public.produtos SET quantidade = quantidade + OLD.quantidade WHERE id = OLD.produto_id;
      SELECT quantidade INTO estoque_atual FROM public.produtos WHERE id = NEW.produto_id;
      IF estoque_atual IS NULL THEN
        RAISE EXCEPTION 'Produto não encontrado ao trocar o produto.';
      END IF;
      IF estoque_atual < NEW.quantidade THEN
        RAISE EXCEPTION 'Estoque insuficiente ao trocar o produto.';
      END IF;
      UPDATE public.produtos SET quantidade = quantidade - NEW.quantidade WHERE id = NEW.produto_id;
      RETURN NEW;
    END IF;

    diferenca := NEW.quantidade - OLD.quantidade;
    IF diferenca > 0 THEN
      SELECT quantidade INTO estoque_atual FROM public.produtos WHERE id = NEW.produto_id;
      IF estoque_atual IS NULL THEN
        RAISE EXCEPTION 'Produto não encontrado ao atualizar quantidade.';
      END IF;
      IF estoque_atual < diferenca THEN
        RAISE EXCEPTION 'Estoque insuficiente ao aumentar quantidade.';
      END IF;
      UPDATE public.produtos SET quantidade = quantidade - diferenca WHERE id = NEW.produto_id;
    ELSIF diferenca < 0 THEN
      UPDATE public.produtos SET quantidade = quantidade + (OLD.quantidade - NEW.quantidade) WHERE id = NEW.produto_id;
    END IF;
    RETURN NEW;

  ELSIF TG_OP = 'DELETE' THEN
    UPDATE public.produtos SET quantidade = quantidade + OLD.quantidade WHERE id = OLD.produto_id;
    RETURN OLD;
  END IF;

  RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS tr_atualiza_estoque ON public.itens_pedido;

CREATE TRIGGER tr_atualiza_estoque
BEFORE INSERT OR UPDATE OR DELETE ON public.itens_pedido
FOR EACH ROW
EXECUTE PROCEDURE public.fn_atualizar_estoque();

-- ============================================================
-- RLS DESABILITADO (desenvolvimento)
-- ============================================================
-- NOTE: RLS is disabled for development/testing.
-- For production, re-enable RLS and set up appropriate policies.
-- ============================================================
ALTER TABLE public.clientes DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.produtos DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.pedidos DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.itens_pedido DISABLE ROW LEVEL SECURITY;

-- ============================================================
-- VIEW DETALHADA DE ITENS DE PEDIDO
-- ============================================================
CREATE OR REPLACE VIEW public.itens_pedido_detalhado AS
SELECT 
    ip.id AS item_id,
    ip.pedido_id,
    ped.cliente_id,
    c.nome AS cliente_nome,
    ip.produto_id,
    p.nome AS produto_nome,
    p.categoria AS produto_categoria,
    ip.quantidade,
    ip.preco_unitario,
    (ip.quantidade * ip.preco_unitario) AS total_item,
    (SELECT SUM(quantidade * preco_unitario) FROM public.itens_pedido WHERE pedido_id = ped.id) AS total_pedido,
    ped.status AS status_pedido,
    ped.criado_em AS criado_em_pedido
FROM public.itens_pedido ip
JOIN public.produtos p ON ip.produto_id = p.id
JOIN public.pedidos ped ON ip.pedido_id = ped.id
JOIN public.clientes c ON ped.cliente_id = c.id;



-- ============================================================
-- FUNÇÃO RPC PARA BUSCA DE PRODUTOS 
-- ============================================================
CREATE OR REPLACE FUNCTION public.buscar_produtos(
    p_nome TEXT DEFAULT NULL,
    p_categoria TEXT DEFAULT NULL,
    p_preco_min NUMERIC DEFAULT NULL,
    p_preco_max NUMERIC DEFAULT NULL,
    p_estoque_min INT DEFAULT NULL,
    p_ordenar_by TEXT DEFAULT 'id',
    p_ordenar_dir TEXT DEFAULT 'asc'
)
RETURNS TABLE (
    id BIGINT,
    nome TEXT,
    preco NUMERIC,
    quantidade INT,
    categoria TEXT,
    criado_em TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE
    sql_query TEXT;
    v_nome TEXT := NULL;
    v_categoria TEXT := NULL;
    v_order_by TEXT;
    v_order_dir TEXT;
BEGIN
    -- Normaliza strings vazias para NULL
    IF p_nome IS NOT NULL AND btrim(p_nome) <> '' THEN
        v_nome := p_nome;
    END IF;

    IF p_categoria IS NOT NULL AND btrim(p_categoria) <> '' THEN
        v_categoria := p_categoria;
    END IF;

    -- 🚨 SE TODOS OS PARÂMETROS FOREM NULL → NÃO RETORNAR NADA
    IF v_nome IS NULL
       AND v_categoria IS NULL
       AND p_preco_min IS NULL
       AND p_preco_max IS NULL
       AND p_estoque_min IS NULL THEN
        RETURN;  -- retorna tabela vazia
    END IF;

    sql_query := 'SELECT id, nome, preco, quantidade, categoria, criado_em
                  FROM public.produtos
                  WHERE ($1 IS NULL OR nome ILIKE ''%'' || $1 || ''%'')
                    AND ($2 IS NULL OR categoria ILIKE ''%'' || $2 || ''%'')
                    AND ($3 IS NULL OR preco >= $3)
                    AND ($4 IS NULL OR preco <= $4)
                    AND ($5 IS NULL OR quantidade >= $5)';

    -- Ordenação segura
    CASE lower(coalesce(p_ordenar_by, 'id'))
      WHEN 'id' THEN v_order_by := 'id';
      WHEN 'nome' THEN v_order_by := 'nome';
      WHEN 'preco' THEN v_order_by := 'preco';
      WHEN 'quantidade' THEN v_order_by := 'quantidade';
      WHEN 'categoria' THEN v_order_by := 'categoria';
      WHEN 'criado_em' THEN v_order_by := 'criado_em';
      ELSE v_order_by := 'id';
    END CASE;

    IF lower(coalesce(p_ordenar_dir, 'asc')) = 'desc' THEN
      v_order_dir := 'DESC';
    ELSE
      v_order_dir := 'ASC';
    END IF;

    sql_query := sql_query || ' ORDER BY ' || v_order_by || ' ' || v_order_dir;

    RETURN QUERY EXECUTE sql_query
      USING v_nome, v_categoria, p_preco_min, p_preco_max, p_estoque_min;
END;
$$;

CREATE OR REPLACE FUNCTION public.listar_por_categoria(
    p_categoria TEXT
)
RETURNS TABLE (
    id BIGINT,
    nome TEXT,
    preco NUMERIC,
    quantidade INT,
    categoria TEXT,
    criado_em TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        id,
        nome,
        preco,
        quantidade,
        categoria,
        criado_em
    FROM public.produtos
    WHERE categoria = p_categoria;  -- FILTRO EXATO, sem ILIKE
END;
$$;

-- NOTE: Examples for calling the REST API with a service role key must
-- live in your backend code (e.g. Python/Node). Removed the embedded
-- Python example to keep this file valid SQL. Use a server-side
-- implementation that reads `SUPABASE_SERVICE_ROLE_KEY` from environment
-- variables and performs writes when necessary.
