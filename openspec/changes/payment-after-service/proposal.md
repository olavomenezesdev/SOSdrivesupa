# Proposal

## Why

Após o prestador concluir um Chamado, o motorista ainda não possui uma etapa de pagamento integrada ao SOS Drive. A tela deve permitir revisar o atendimento e escolher uma forma de pagamento real antes de finalizar o fluxo.

## What Changes

- Criar uma tela de pagamento após o status `completed` do Chamado, com visual equivalente à referência fornecida e resumo visual registrado pelo app.
- Mostrar serviço, prestador, veículo, distância, data do Chamado e total persistido.
- Oferecer somente cartão de crédito por meio de Checkout hospedado seguro pelo Asaas; os dados de cartão são coletados diretamente no checkout, não no SOS Drive.
- Manter o Prestador na tela de aguardando pagamento enquanto a cobrança não estiver confirmada.
- Após confirmação, abrir telas distintas de avaliação para Motorista e Prestador.
- Registrar no saldo interno do Prestador o valor total do serviço uma única vez após a confirmação oficial do pagamento; não realizar transferência automática para banco ou conta Asaas.
- Após a confirmação do pagamento, manter o fluxo do Motorista para avaliação e, depois do envio ou reconhecimento da avaliação existente, retornar a `/home_client`.
- Permitir que cada parte avalie a outra e publique nota/comentário no perfil correspondente.
- Integrar a criação e confirmação de cobranças com Asaas sandbox por configuração de ambiente segura.
- Reconciliar pagamentos pendentes consultando a API autenticada do Asaas quando uma atualização manual não puder depender do webhook.
- Restringir a autorização e os dados exibidos ao proprietário do Chamado.
- Não armazenar credenciais do Asaas no repositório, interface ou logs.

## Capabilities

### New Capabilities

- `payment-after-service`: pagamento do atendimento concluído, com resumo, Checkout de cartão e confirmação segura.

### Modified Capabilities

Nenhuma.

## Impact

- Dentro do escopo do MVP: segue o ciclo de atendimento e adiciona pagamento ao pedido concluído.
- Atualiza o fluxo do Chamado sem alterar seus status estruturais.
- Acrescenta um saldo interno de ganhos do Prestador vinculado a pagamentos confirmados; o saldo exibido não representa liquidação ou saque automático.
- Introduz Asaas como gateway externo em ambiente sandbox; a tecnologia principal permanece Python/Reflex.
- A chave `ASAAS_API_KEY` será mantida fora do repositório e no ambiente de execução.
- Não altera cadastro, avaliação, localização ou funcionalidade não relacionada.
- Inclui migrações incrementais para pagamentos/Checkout e avaliações.
