@app.get("/itens-pedido-detalhado/{pedido_id}")
async def itens_pedido_detalhado(pedido_id: int):
    async with httpx.AsyncClient(timeout=10) as client:
        # 1) Buscar pedido
        r_pedido = await client.get(f"{POSTGREST_URL}/{PEDIDOS_TABLE}",
                                    headers=postgrest_headers(),
                                    params={"id": f"eq.{pedido_id}"})
        if r_pedido.status_code >= 400:
            raise HTTPException(r_pedido.status_code, r_pedido.text)
        pedido_list = r_pedido.json()
        if not pedido_list:
            raise HTTPException(404, "Pedido não encontrado")
        pedido = pedido_list[0]

        # 2) Buscar cliente
        r_cliente = await client.get(f"{POSTGREST_URL}/{CLIENTES_TABLE}",
                                     headers=postgrest_headers(),
                                     params={"id": f"eq.{pedido['cliente_id']}"})
        cliente_list = r_cliente.json() if r_cliente.status_code < 400 else []
        cliente_nome = cliente_list[0]['nome'] if cliente_list else None

        # 3) Buscar itens
        r_itens = await client.get(f"{POSTGREST_URL}/{ITENS_PEDIDO_TABLE}",
                                   headers=postgrest_headers(),
                                   params={"pedido_id": f"eq.{pedido_id}"})
        itens = r_itens.json() if r_itens.status_code < 400 else []

        # 4) Adicionar informações detalhadas em cada item
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
