import os
from typing import Optional, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx

load_dotenv()

# CORRIGIDO: estava SUPABASE_URLL
SUPABASE_URL = os.getenv("SUPABASE_URL")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
POSTGREST_URL = f"{SUPABASE_URL}/rest/v1"

# Nomes das tabelas
CLIENTES_TABLE = "clientes"
PRODUTOS_TABLE = "produtos"
PEDIDOS_TABLE = "pedidos"
ITENS_PEDIDO_TABLE = "itens_pedido"

if not SUPABASE_URL or not ANON_KEY:
    raise RuntimeError("Configure SUPABASE_URL e SUPABASE_ANON_KEY no .env")

app = FastAPI(title="API de Compras (FastAPI + Supabase)")

# ==================== MODELOS ====================

class ClienteCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=255)
    email: str
    telefone: Optional[str] = None

class ClienteUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=3, max_length=255)
    email: Optional[str] = None
    telefone: Optional[str] = None

class ClienteOut(BaseModel):
    id: int
    nome: str
    email: str
    telefone: Optional[str]
    criado_em: str

class ProdutoCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=255)
    preco: float = Field(gt=0)
    quantidade: int = Field(ge=0)
    categoria: Optional[str] = None

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=3, max_length=255)
    preco: Optional[float] = Field(default=None, gt=0)
    quantidade: Optional[int] = Field(default=None, ge=0)
    categoria: Optional[str] = None

class ProdutoOut(BaseModel):
    id: int
    nome: str
    preco: float
    quantidade: int
    categoria: Optional[str]
    criado_em: str

class ItensPedidoCreate(BaseModel):
    pedido_id: int
    produto_id: int
    quantidade: int = Field(gt=0)
    preco_unitario: float = Field(gt=0)

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

class PedidoCreate(BaseModel):
    cliente_id: int
    status: Optional[str] = "pendente"

class PedidoUpdate(BaseModel):
    status: Optional[str] = None

class PedidoOut(BaseModel):
    id: int
    cliente_id: int
    total: float
    status: str
    criado_em: str


# Modelo para criar pedido + itens em uma única chamada (server-side)
class PedidoItemCreate(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0)
    preco_unitario: float = Field(gt=0)


class PedidoWithItemsCreate(BaseModel):
    cliente_id: int
    status: Optional[str] = "pendente"
    itens: List[PedidoItemCreate]

# ==================== HELPERS ====================

def postgrest_headers(api_key: str = ANON_KEY):
    return {
        "apikey": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health():
    return {"status": "ok"}

# ==================== CLIENTES ====================

@app.get("/clientes", response_model=List[ClienteOut])
async def list_clientes(limit: int = 50, offset: int = 0):
    params = {
        "select": "*",
        "limit": str(limit),
        "offset": str(offset),
        "order": "criado_em.desc"
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{CLIENTES_TABLE}", headers=postgrest_headers(), params=params)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.get("/clientes/{cliente_id}", response_model=List[ClienteOut])
async def get_cliente(cliente_id: int):
    params = {"select": "*", "id": f"eq.{cliente_id}"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{CLIENTES_TABLE}", headers=postgrest_headers(), params=params)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.post("/clientes", response_model=List[ClienteOut], status_code=201)
async def create_cliente(payload: ClienteCreate):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{POSTGREST_URL}/{CLIENTES_TABLE}",
            headers=postgrest_headers(),
            json=payload.model_dump()
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.put("/clientes/{cliente_id}", response_model=List[ClienteOut])
async def update_cliente(cliente_id: int, payload: ClienteUpdate):
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(400, "No fields to update")

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.patch(
            f"{POSTGREST_URL}/{CLIENTES_TABLE}",
            headers=postgrest_headers(),
            params={"id": f"eq.{cliente_id}"},
            json=data,
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.delete("/clientes/{cliente_id}", status_code=204)
async def delete_cliente(cliente_id: int):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.delete(
            f"{POSTGREST_URL}/{CLIENTES_TABLE}",
            headers=postgrest_headers(),
            params={"id": f"eq.{cliente_id}"}
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return {}

# ==================== PRODUTOS ====================

@app.get("/produtos", response_model=List[ProdutoOut])
async def list_produtos(limit: int = 50, offset: int = 0):
    params = {
        "select": "*",
        "limit": str(limit),
        "offset": str(offset),
        "order": "criado_em.desc"
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{PRODUTOS_TABLE}", headers=postgrest_headers(), params=params)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.get("/produtos/{produto_id}", response_model=List[ProdutoOut])
async def get_produto(produto_id: int):
    params = {"select": "*", "id": f"eq.{produto_id}"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{PRODUTOS_TABLE}", headers=postgrest_headers(), params=params)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.post("/produtos", response_model=List[ProdutoOut], status_code=201)
async def create_produto(payload: ProdutoCreate):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{POSTGREST_URL}/{PRODUTOS_TABLE}",
            headers=postgrest_headers(),
            json=payload.model_dump()
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.put("/produtos/{produto_id}", response_model=List[ProdutoOut])
async def update_produto(produto_id: int, payload: ProdutoUpdate):
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(400, "No fields to update")

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.patch(
            f"{POSTGREST_URL}/{PRODUTOS_TABLE}",
            headers=postgrest_headers(),
            params={"id": f"eq.{produto_id}"},
            json=data,
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.delete("/produtos/{produto_id}", status_code=204)
async def delete_produto(produto_id: int):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.delete(
            f"{POSTGREST_URL}/{PRODUTOS_TABLE}",
            headers=postgrest_headers(),
            params={"id": f"eq.{produto_id}"}
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return {}

# ==================== PEDIDOS ====================

@app.get("/pedidos", response_model=List[PedidoOut])
async def list_pedidos(limit: int = 50, offset: int = 0):
    params = {
        "select": "*",
        "limit": str(limit),
        "offset": str(offset),
        "order": "criado_em.desc"
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{PEDIDOS_TABLE}", headers=postgrest_headers(), params=params)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.get("/pedidos/{pedido_id}", response_model=List[PedidoOut])
async def get_pedido(pedido_id: int):
    params = {"select": "*", "id": f"eq.{pedido_id}"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{PEDIDOS_TABLE}", headers=postgrest_headers(), params=params)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.post("/pedidos", response_model=List[PedidoOut], status_code=201)
async def create_pedido(payload: PedidoCreate):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{POSTGREST_URL}/{PEDIDOS_TABLE}",
            headers=postgrest_headers(),
            json=payload.model_dump()
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()


@app.post("/service/pedidos", response_model=List[PedidoOut], status_code=201)
async def create_pedido_service(payload: PedidoWithItemsCreate):
    """Create a pedido and its items using the SERVICE_ROLE_KEY (server-side).

    This bypasses RLS and should be used only from a trusted server.
    """
    if not SERVICE_ROLE_KEY:
        raise HTTPException(500, "SUPABASE_SERVICE_ROLE_KEY is not configured on the server")

    service_headers = postgrest_headers(SERVICE_ROLE_KEY)

    # 1) create pedido
    pedido_data = {"cliente_id": payload.cliente_id, "status": payload.status}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"{POSTGREST_URL}/{PEDIDOS_TABLE}", headers=service_headers, json=pedido_data)
        if r.status_code >= 400:
            raise HTTPException(r.status_code, f"Failed creating pedido: {r.text}")
        created = r.json()
        if not created or not isinstance(created, list):
            raise HTTPException(500, "Unexpected response when creating pedido")
        pedido_id = created[0].get("id")

        # 2) create itens_pedido
        try:
            itens_payload = []
            for it in payload.itens:
                itens_payload.append({
                    "pedido_id": pedido_id,
                    "produto_id": it.produto_id,
                    "quantidade": it.quantidade,
                    "preco_unitario": it.preco_unitario,
                })

            # insert items one by one to leverage triggers and get per-item errors
            created_items = []
            for item in itens_payload:
                r2 = await client.post(f"{POSTGREST_URL}/{ITENS_PEDIDO_TABLE}", headers=service_headers, json=item)
                if r2.status_code >= 400:
                    raise HTTPException(r2.status_code, f"Failed creating item: {r2.text}")
                created_items.extend(r2.json())

        except HTTPException:
            # attempt basic rollback: delete the pedido we created
            await client.delete(f"{POSTGREST_URL}/{PEDIDOS_TABLE}", headers=service_headers, params={"id": f"eq.{pedido_id}"})
            raise

    # Return the created pedido representation (fresh from DB)
    async with httpx.AsyncClient(timeout=10) as client:
        r_final = await client.get(f"{POSTGREST_URL}/{PEDIDOS_TABLE}", headers=service_headers, params={"id": f"eq.{pedido_id}"})
    if r_final.status_code >= 400:
        raise HTTPException(r_final.status_code, r_final.text)
    return r_final.json()

@app.put("/pedidos/{pedido_id}", response_model=List[PedidoOut])
async def update_pedido(pedido_id: int, payload: PedidoUpdate):
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(400, "No fields to update")

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.patch(
            f"{POSTGREST_URL}/{PEDIDOS_TABLE}",
            headers=postgrest_headers(),
            params={"id": f"eq.{pedido_id}"},
            json=data,
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.delete("/pedidos/{pedido_id}", status_code=204)
async def delete_pedido(pedido_id: int):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.delete(
            f"{POSTGREST_URL}/{PEDIDOS_TABLE}",
            headers=postgrest_headers(),
            params={"id": f"eq.{pedido_id}"}
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return {}

# ==================== ITENS DO PEDIDO ====================

@app.get("/itens-pedido", response_model=List[ItensPedidoOut])
async def list_itens_pedido(limit: int = 50, offset: int = 0):
    params = {
        "select": "*",
        "limit": str(limit),
        "offset": str(offset)
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{ITENS_PEDIDO_TABLE}", headers=postgrest_headers(), params=params)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.get("/itens-pedido/{item_id}", response_model=List[ItensPedidoOut])
async def get_item_pedido(item_id: int):
    params = {"select": "*", "id": f"eq.{item_id}"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{POSTGREST_URL}/{ITENS_PEDIDO_TABLE}",
            headers=postgrest_headers(),
            params=params
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()


@app.get("/pedidos/{pedido_id}/itens", response_model=List[ItensPedidoOut])
async def get_itens_pedido_by_pedido(pedido_id: int):
    params = {"select": "*", "pedido_id": f"eq.{pedido_id}"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{POSTGREST_URL}/{ITENS_PEDIDO_TABLE}", headers=postgrest_headers(), params=params)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()


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

        # Adicionar nome do produto em cada item
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

@app.post("/itens-pedido", response_model=List[ItensPedidoOut], status_code=201)
async def create_item_pedido(payload: ItensPedidoCreate):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{POSTGREST_URL}/{ITENS_PEDIDO_TABLE}",
            headers=postgrest_headers(),
            json=payload.model_dump()
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()

@app.delete("/itens-pedido/{item_id}", status_code=204)
async def delete_item_pedido(item_id: int):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.delete(
            f"{POSTGREST_URL}/{ITENS_PEDIDO_TABLE}",
            headers=postgrest_headers(),
            params={"id": f"eq.{item_id}"}
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return {}
