# API_-Compras

API de Compras (FastAPI + Supabase)  

---

## 📘 Resumo e Objetivo

A **API de Compras** é um sistema simples para cadastro de **clientes**, **produtos**, **pedidos** e **itens de pedidos**, funcionando totalmente via **REST** usando **Supabase** (PostgREST).  

**Objetivo:**  
- Organizar informações de clientes  
- Registrar pedidos e itens  
- Consultar rapidamente dados de vendas  
- Servir como base para sistemas de vendas, e-commerce ou ERP simples  

Fluxo lógico da API:  
**Cliente → Pedido → Itens do Pedido**  

---

## ⚙️ Como rodar (básico)

1. Clonar o repositório:  
bash
git clone https://github.com/felipe370-hub/API_-Compras.git
cd API_-Compras
Instalar dependências:

bash
Copiar código
pip install -r requirements.txt
Configurar variáveis de ambiente no .env:

env
Copiar código
SUPABASE_URL=https://<sua-url>.supabase.co
SUPABASE_ANON_KEY=<sua-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<sua-service-role-key>
Rodar a API:

bash
Copiar código
uvicorn main:app --reload
Verificar health check:

http
Copiar código
GET /health

  "status": "ok"

---
## 🌐 Endpoints e Rotas
👤 Clientes
Listar clientes
GET /clientes

Exemplo de resposta:

  {
    "id": 1,
    "nome": "João da Silva",
    "email": "joao@example.com",
    "telefone": "11999999999",
    "criado_em": "2025-11-30T03:00:00Z"
  }
  
Criar cliente
POST /clientes

{
  "nome": "João da Silva",
  "email": "joao@example.com",
  "telefone": "11999999999"
}




Copiar código
{
  "id": 2,
  "nome": "João da Silva",
  "email": "joao@example.com",
  "telefone": "11999999999",
  "criado_em": "2025-11-30T03:15:00Z"
}
---
## 📦 Produtos
Listar produtos
GET /produtos


  {
    "id": 1,
    "nome": "Brigadeiro",
    "categoria": "Doce",
    "preco": 9.90,
    "quantidade": 50,
    "criado_em": "2025-11-30T03:10:00Z"
  }





Criar produto
POST /produtos




{
  "nome": "Brigadeiro",
  "categoria": "Doce",
  "preco": 9.90,
  "quantidade": 50
}





{
  "id": 2,
  "nome": "Brigadeiro",
  "categoria": "Doce",
  "preco": 9.90,
  "quantidade": 50,
  "criado_em": "2025-11-30T03:20:00Z"
}


---


## 🧾 Pedidos
Listar pedidos
GET /pedidos





  {
    "id": 1,
    "cliente_id": 1,
    "total": 0,
    "status": "aberto",
    "criado_em": "2025-11-30T03:25:00Z"
  }




Criar pedido
POST /pedidos





{
  "cliente_id": 1,
  "total": 0,
  "status": "aberto"
}





{
  "id": 2,
  "cliente_id": 1,
  "total": 0,
  "status": "aberto",
  "criado_em": "2025-11-30T03:30:00Z"
}

Detalhe detalhado de um pedido
GET /pedidos/{pedido_id}/detalhe_detalhado




  {
    "id": 1,
    "pedido_id": 1,
    "produto_id": 1,
    "quantidade": 2,
    "preco_unitario": 9.90,
    "produto_nome": "Brigadeiro",
    "produto_categoria": "Doce",
    "cliente_nome": "João da Silva",
    "total_item": 19.8,
    "total_pedido": 19.8,
    "status_pedido": "aberto",
    "criado_em_pedido": "2025-11-30T03:25:00Z"
  }



---


## 📑 Itens do Pedido
Listar itens do pedido
GET /itens-pedido

Criar item do pedido
POST /itens-pedido






{
  "pedido_id": 1,
  "produto_id": 2,
  "quantidade": 3,
  "preco_unitario": 50.0
}





{
  "id": 1,
  "pedido_id": 1,
  "produto_id": 2,
  "quantidade": 3,
  "preco_unitario": 50.0
}



---



✅ Observações importantes
cliente_id deve existir na tabela clientes.

produto_id deve existir na tabela produtos.

Rotas funcionam conforme descrito acima.

🔗 Link do Deploy Render
https://api-compras-1.onrender.com
