# API_-Compras
api de compras

📘 API de Compras – Documentação Completa

A API de Compras é um sistema simples para cadastro de clientes, pedidos e itens de pedido, funcionando de forma totalmente REST usando o Supabase (PostgREST).
Ela permite criar um fluxo básico de vendas:

Cadastrar um cliente

Criar um pedido para esse cliente

Adicionar itens dentro do pedido

Consultar pedidos, clientes e itens


🎯 Objetivo da API

Esta API tem como objetivo:

Organizar informações de clientes

Registrar pedidos feitos pelos clientes

Registrar itens dentro de cada pedido

Permitir consultas rápidas de todos esses dados

Servir como base para sistemas de vendas, e-commerce ou ERP simples

Ela funciona sem backend próprio — o Supabase já gera automaticamente os endpoints usando sua camada REST.

🧱 Como a API funciona internamente

A API é baseada em três tabelas principais:

1️⃣ Usuarios

Guarda informações das pessoas que fazem pedidos.

Exemplo:

João da Silva

maria@email.com

(11) 99999-9999

2️⃣ pedidos

Cada pedido pertence a um cliente.

Exemplo:

Pedido #1 → Cliente 1

Data: 2025-01-01

Status: “aberto”

4:Produtos
Onde irá cadastrar os produtos da sua loja( modelo de loja você escolhe)
  {
  "nome" : "Brigadeiro",
  "categoria": "Doce",
  "preco": 9.90,
  "quantidade": 50
  }
e quando cadastrar, aparecerá o numero do id automaticamente ficamdo assim
    {
        "id": 4,
        "cliente_id": 1,
        "total": 0,
        "status": "pendente",
        "criado_em": "2025-11-30T03:28:59.008224+00:00"
    }

3️ itens_pedido

Cada item pertence a um pedido.

Exemplo:

Produto: Camiseta, mas vais ser refirida pela id gerada no Produtos

  "pedido_id":3 ,
  "produto_id": 1,
  "quantidade": 1,
  "preco_unitario": 25.9

E quando entrar dentro de itens_pedido_detalhado, irá mostrar detaladamente o seu pedido:
    {
        "item_id": 1,
        "pedido_id": 3,
        "cliente_id": 1,
        "cliente_nome": "Felipe Davids",
        "produto_id": 1,
        "produto_nome": "Hamburguer",
        "produto_categoria": "Salgado",
        "quantidade": 1,
        "preco_unitario": 25.9,
        "total_item": 25.9,
        "total_pedido": 51.8,
        "status_pedido": "pendente",
        "criado_em_pedido": "2025-11-30T02:47:20.190142+00:00"
    },



🔄 Fluxo lógico da API (visão simples)
Cliente → faz → Pedido → contém → Itens


Ou seja:
✔ Primeiro a loja irá disponibilizar os produtos
✔ Segundo cria o cliente
✔ Depois cria um pedido para esse cliente
✔ Depois adiciona itens dentro desse pedido

Assim, tudo fica organizado e relacionado.

🌐 URL Base da API

👉 INSIRA AQUI SUA URL DO SUPABASE REST

https://xoveqvqgwquqmrlxskwn.supabase.co/rest/v1


Cada endpoint é acessado adicionando o nome da tabela no final da URL.

🧪 Como fazer requisições (explicação simples)

Você usa métodos HTTP:

Método	Para que serve
GET	Buscar dados
POST	Criar novo registro
PATCH	Atualizar registro
DELETE	Apagar registro

Exemplo:

GET /clientes
POST /pedidos
POST /itens_pedido


Todas as requisições são JSON.

📌 Endpoints explicados

Aqui está cada rota explicada de forma simples para quem nunca viu a API.

👤 1. CLIENTES
➤ O que é?

Pessoas que fazem pedidos.

➤ Para que serve?

Antes de criar um pedido, você precisa de um cliente.

✔ GET - Listar clientes
GET /clientes


Retorna todos os clientes cadastrados.

✔ POST - Criar cliente
POST /clientes
Content-Type: application/json

{
  "nome": "João da Silva",
  "email": "joao@example.com",
  "telefone": "11999999999"
}

📦 2. PEDIDOS
➤ O que é?

Um pedido criado por um cliente.

Cada pedido pertence a um cliente específico (cliente_id).

✔ GET - Listar pedidos
GET /pedidos

✔ POST - Criar pedido
POST /pedidos
Content-Type: application/json

{
  "cliente_id": 1,
  "data_pedido": "2025-01-01T10:00:00",
  "status": "aberto"
}


⚠ cliente_id deve existir na tabela clientes.

🧰 3. ITENS DO PEDIDO
➤ O que é?

Produtos/serviços adicionados dentro de um pedido.

✔ GET - Listar itens
GET /itens_pedido

✔ POST - Criar item
POST /itens_pedido
Content-Type: application/json

{
  "pedido_id": 1,
  "descricao": "Produto X",
  "quantidade": 2,
  "valor_unitario": 50.00,
  "sub_total": 100.00
}
✔ POST - {{path}}/rest/v1/rpc/buscar_produtos
e assim vc colocara qualquer variavel
{
  "p_nome": "",
  "p_categoria": ""
}
irá retonar o que você tanto procura na lista de Produtos
⚠ pedido_id deve existir na tabela pedidos.

🧭 Ordem recomendada de uso (explicado para iniciantes)
1️⃣ Criar um cliente

↓

2️⃣ Criar um pedido para esse cliente

↓

3️⃣ Adicionar itens ao pedido

↓

4️⃣ Consultar relatórios (GET)

Isso simula o comportamento real de um sistema de vendas.
lik do render
link do 
