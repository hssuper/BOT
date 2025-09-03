-- Lógica do Servidor Lua para receber a notificação
-- A maioria dos frameworks de RP tem uma forma de criar APIs HTTP.
-- Aqui está um exemplo conceitual:

RegisterNetEvent("API:DarItem") -- Cria um evento para a API

AddEventHandler("API:DarItem", function(source, body)
    local user_id = body.user_id
    local itens = body.itens
    local token = body.token

    -- 1. Verifica a segurança
    if token ~= "seu-token-secreto" then
        print("Erro de segurança: Token inválido.")
        return
    end

    -- 2. Credita cada item comprado
    for i, item_chave in ipairs(itens) do
        darItemAoUsuario(user_id, item_chave)
    end
end)

-- Seu servidor Lua agora precisa de uma forma de receber HTTP POSTs
-- e chamar este evento. Exemplo conceitual (depende do seu framework):
-- local my_http_server = CreateHttpServer(30120)
-- my_http_server.on("/daritem", function(request, response)
--     local body = json.decode(request.body)
--     TriggerEvent("API:DarItem", source, body)
--     response:send("OK")
-- end)