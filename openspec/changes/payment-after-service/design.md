# Design

## Context

Veja `proposal.md` e `specs/payment-after-service/spec.md`. O app já identifica Chamados concluídos por `completed`, reutiliza o estado `OperationalState` e possui uma tela básica em `/service-finalized`. A integração precisa acrescentar valor persistido, segurança e status real de cobrança sem mover autorização para o frontend.

## Goals / Non-Goals

**Goals:**

- Reutilizar o layout e os dados já carregados do Chamado concluído.
- Criar cobranças reais de cartão de crédito no Asaas sandbox a partir do backend.
- Exibir o cartão de crédito somente pelo Checkout hospedado seguro do Asaas.
- Persistir relação entre Chamado e cobrança para confirmação e consulta.
- Validar proprietário, valor e estado antes de criar ou confirmar cobrança.
- Entregar uma interface próxima da referência fornecida, sem placeholders visuais no fluxo de cartão.
- Bloquear o prestador na espera até o pagamento confirmado.
- Registrar avaliações mútuas após o pagamento e exibí-las no perfil.
- Registrar e exibir no app os ganhos confirmados do Prestador pelo valor total do serviço.
- Retornar o Motorista à Home do cliente depois da avaliação pós-pagamento.

**Non-Goals:**

- Produção real, split de repasses, saque ou liquidação financeira automática.
- Migração histórica de pagamentos antigos.
- Alterar avaliação, localização, mensagens ou status do Chamado.
- Armazenar dados completos de cartão no banco SOS Drive.

## Decisions

1. **Backend manda a cobrança**
   - Python criará a cobrança no Asaas usando `ASAAS_API_KEY`, ambiente sandbox e `ASAAS_API_URL`.
   - A chave nunca será enviada ao frontend, persistida no banco ou registrada em logs.
   - Alternativa considerada: chamar Asaas no navegador; rejeitada por expor credencial e permitir cobrança não autorizada.

2. **Valor vem do Chamado**
   - O backend localizará o Chamado pela sessão autenticada e pelo identificador informado, verificará `completed` e obterá o valor persistido.
   - A interface pode apresentar estimativas, mas não pode definir o valor cobrado.
   - Alternativa considerada: total calculado no frontend; rejeitada por fraude e divergência.

3. **Persistir cobrança separada**
   - A mudança criará/consumirá uma entidade de pagamento ligada ao Chamado, com identificador Asaas, método, valor, estado e timestamps.
   - Essa entidade não altera os dados estruturais de Chamado, Motorista, Prestador ou Avaliação.
   - Alternativa considerada: não persistir; rejeitada por não permitir conferência e atualização de status.

4. **Webhook como via principal e reconciliação autenticada como fallback**
   - Webhooks autenticados do Asaas permanecem a via principal de atualização, com processamento idempotente.
   - Ao atualizar manualmente um pagamento pendente, o backend consulta a lista de pagamentos Asaas filtrada pelo identificador do Checkout. Só persiste confirmação quando encontra uma cobrança única, com Checkout e valor correspondentes, em estado `CONFIRMED` ou `RECEIVED`.
   - O frontend nunca confirma pagamento por conta própria; usa somente o estado persistido pelo backend.
   - Redirecionamento do Checkout e estados não liquidados não confirmam pagamentos.

5. **Reutilizar o layout de anexo**
   - A nova tela seguirá o formato atual de cabeçalho, resumo à esquerda e formulário à direita.
   - O Checkout Asaas hospedado coletará os dados do cartão de crédito.
   - Alternativa considerada: nova identidade visual; rejeitada porque a solicitação exige consistência com a tela fornecida.

6. **Cartão de crédito é a única forma de pagamento**
   - O backend cria uma sessão Asaas limitada a cartão de crédito; o usuário informa seus dados diretamente no Checkout hospedado.
   - O SOS Drive não recebe nem mantém PAN, CVV ou validade, reduzindo o escopo PCI do aplicativo.

7. **Prestador aguarda pagamento em tela dedicada**
   - O prestador permanece em `/waiting-payment` ou estado equivalente após `completed` enquanto o pagamento não estiver confirmado.
   - A saída para novos chamados só ocorre após confirmação; a rota seguinte apresenta a avaliação do participante.
   - Alternativa considerada: permitir retorno imediato à Home; rejeitada porque quebra o encerramento financeiro do chamado.

8. **Avaliações persistidas por Chamado**
   - Cada avaliação terá Chamado, avaliador, avaliado, nota e comentário.
   - Unicidade será garantida por combinação de Chamado e avaliador.
   - Perfis consultarão avaliações recebidas e calcularão média; o backend aplicará autorização.

9. **Saldo interno do Prestador**
   - O backend registra um lançamento de ganho associado ao Chamado e ao pagamento, usando o valor total persistido do serviço.
   - O lançamento só é criado quando o backend confirma o pagamento por webhook autorizado ou reconciliação autenticada; estados pendentes, falhos ou cancelados não geram saldo.
   - O identificador do Chamado deve ser único nos lançamentos de ganho para que webhooks repetidos e reconciliações não creditem o mesmo serviço mais de uma vez.
   - O saldo exibido na conta do Prestador é a soma dos lançamentos confirmados. Ele é informativo dentro do app e não implica transferência bancária, saque ou repasse automático.
   - Alternativa considerada: creditar ao receber o retorno do Checkout; rejeitada porque o retorno do navegador não comprova liquidação.

10. **Retorno do Motorista depois do pagamento**
    - Após a confirmação, o Motorista segue para a avaliação; depois de enviar ou reconhecer uma avaliação existente, retorna a `/home_client`.
    - O saldo do Prestador é atualizado pela confirmação persistida e aparece na conta do Prestador, sem alterar a etapa de avaliação.

## Risks / Trade-offs

- [A chave fornecida pode estar associada a ambiente não esperado] → validar o ambiente sandbox antes da integração e nunca registrar o segredo.
- [O Checkout de cartão pode ser recusado pelo Asaas] → exibir estado pendente ou falha com segurança e depender do webhook autorizado para confirmar.
- [Webhook pode ser duplicado ou chegar fora de ordem] → processar por identificador único e transições idempotentes.
- [Cobrança pode existir antes da persistência local] → gravar estado mínimo imediatamente e reconciliar por identificador.
- [Eventos de confirmação podem ser repetidos] → garantir unicidade do lançamento de ganho por Chamado e derivar o saldo dos lançamentos persistidos.
- [Cartão pode exigir tokenização segura] → usar o fluxo suportado pelo Asaas, sem armazenar PAN ou CVV no banco.

## Migration Plan

1. Criar configuração segura e migrações para pagamentos e lançamentos de ganhos.
2. Implementar criação/consulta/cancelamento de cobrança e contabilização idempotente no backend.
3. Registrar webhook do Asaas e testes sandbox.
4. Integrar as telas Reflex de pagamento e saldo do Prestador após confirmação `completed`.
5. Reverter pelo desligamento da nova rota e desativação do webhook; não há alteração em dados históricos de Chamado.

## Open Questions

- Nenhuma decisão material permanece aberta para iniciar sandbox.
