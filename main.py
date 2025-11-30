import os
from typing import Optional, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

load_dotenv()

# ------------------- CONFIGURAÇÃO SUPABASE -------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
POSTGREST_URL = f"{SUPABASE_URL}/rest/v1"

CLIENTES_TABLE = "clientes"
PRODUTOS_TABLE = "produtos"
PEDIDOS_TABLE = "pedidos"
ITENS_PEDIDO_TABLE = "itens_pedido"

if not SUPABASE_URL or not ANON_KEY:
    raise RuntimeError("Configure SUPABASE_URL e SUPABASE_ANON_KEY no .env")

# ------------------- INSTÂNCIA FASTAPI -------------------
app = FastAPI(title="API de Compras (FastAPI + Supabase)")

# ------------------- MODELOS -------------------
class ClienteOut(BaseModel):
    id: int
    nome: str
    email: str
    telefone: Optional[str]
    criado_em: str

class ProdutoOut(BaseModel):
    id: int
    nome: str
    preco: float
    quantidade: int
    categoria: Optional[str]
    criado_em: str

class PedidoOut(BaseModel):
    id: int
    cliente_id: int
    total: float
    status: str
    criado_em: str

class ItensPedidoOut(BaseModel):
    id: int
    pedido_id: int
    produto_id: int
    quantidade: int
    preco_unitario: float

class ItensPedidoDetalhado(BaseModel):
    id: int
    pedido_id: int
    produto_id: int
    quantidade: int
    preco_unitario: float
    produto_nome: Optional[str] = None
    produto_categoria: Optional[str] = None
    cliente_nome: Optional[str] = None
    total_item: float
    total_pedido: float
    status_pedido: str
    criado_em_pedido: str

# ------------------- HELPERS -------------------
def postgrest_headers(api_key: str = ANON_KEY):
    return {
        "apikey": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }

# ------------------- HEALTH CHECK -------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# ------------------- ROTAS CLIENTES -------------------
@app.get("/clientes", response_model=List[ClienteOut])
async def list_clientes(limit: int = 50, offset: int = 0):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{CLIENTES_TABLE}", 
                             headers=postgrest_headers(),
                             params={"select": "*", "limit": str(limit), "offset": str(offset)})
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

# ------------------- ROTAS PRODUTOS -------------------
@app.get("/produtos", response_model=List[ProdutoOut])
async def list_produtos(limit: int = 50, offset: int = 0):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{PRODUTOS_TABLE}", 
                             headers=postgrest_headers(),
                             params={"select": "*", "limit": str(limit), "offset": str(offset)})
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

# ------------------- ROTAS PEDIDOS -------------------
@app.get("/pedidos", response_model=List[PedidoOut])
async def list_pedidos(limit: int = 50, offset: int = 0):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{PEDIDOS_TABLE}", 
                             headers=postgrest_headers(),
                             params={"select": "*", "limit": str(limit), "offset": str(offset)})
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

# ------------------- ROTAS ITENS PEDIDO -------------------
@app.get("/itens-pedido", response_model=List[ItensPedidoOut])
async def list_itens_pedido(limit: int = 50, offset: int = 0):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{ITENS_PEDIDO_TABLE}", 
                             headers=postgrest_headers(),
                             params={"select": "*", "limit": str(limit), "offset": str(offset)})
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

# ------------------- ROTA DETALHE DETALHADO -------------------
@app.get("/pedidos/{pedido_id}/detalhe_detalhado", response_model=List[ItensPedidoDetalhado])
async def detalhe_detalhado(pedido_id: int):
    async with httpx.AsyncClient(timeout=10) as client:
        # Buscar pedido
        r_pedido = await client.get(f"{POSTGREST_URL}/{PEDIDOS_TABLE}",
                                    headers=postgrest_headers(),
                                    params={"id": f"eq.{pedido_id}"})
        if r_pedido.status_code >= 400:
            raise HTTPException(r_pedido.status_code, r_pedido.text)
        pedido_list = r_pedido.json()
        if not pedido_list:
            raise HTTPException(404, "Pedido não encontrado")
        pedido = pedido_list[0]

        # Buscar cliente
        r_cliente = await client.get(f"{POSTGREST_URL}/{CLIENTES_TABLE}",
                                     headers=postgrest_headers(),
                                     params={"id": f"eq.{pedido['cliente_id']}"})
        cliente_list = r_cliente.json() if r_cliente.status_code < 400 else []
        cliente_nome = cliente_list[0]['nome'] if cliente_list else None

        # Buscar itens
        r_itens = await client.get(f"{POSTGREST_URL}/{ITENS_PEDIDO_TABLE}",
                                   headers=postgrest_headers(),
                                   params={"pedido_id": f"eq.{pedido_id}"})
        itens = r_itens.json() if r_itens.status_code < 400 else []

        # Adicionar detalhes dos produtos e cliente
        for item in itens:
            r_produto = await client.get(f"{POSTGREST_URL}/{PRODUTOS_TABLE}",
                                         headers=postgrest_headers(),
                                         params={"id": f"eq.{item['produto_id']}"})
            produto_list = r_produto.json() if r_produto.status_code < 400 else []
            item['produto_nome'] = produto_list[0]['nome'] if produto_list else None
            item['produto_categoria'] = produto_list[0]['categoria'] if produto_list else None
            item['cliente_nome'] = cliente_nome
            item['total_item'] = item['quantidade'] * item['preco_unitario']
            item['total_pedido'] = pedido['total']
            item['status_pedido'] = pedido['status']
            item['criado_em_pedido'] = pedido['criado_em']

    return itens
