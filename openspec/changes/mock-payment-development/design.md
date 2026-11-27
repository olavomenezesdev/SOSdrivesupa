## Context

Consulte [proposal.md](./proposal.md) para motivação e [specs/payment-simulation/spec.md](./specs/payment-simulation/spec.md) para o contrato comportamental. O fluxo atual de pagamento e de pós-confirmação já existe; esta mudança introduz apenas uma alternativa para testes com isolamento obrigatório de produção.

## Goals / Non-Goals

**Goals:**

- Fazer o backend selecionar o modo simulado somente com `PAYMENT_MODE=mock` e uma identificação explícita de ambiente de desenvolvimento/teste.
- Reutilizar as validações, a atualização de estado e as etapas pós-pagamento existentes sempre que possível.
- Preservar integralmente o caminho Asaas em produção.

**Non-Goals:**

- Alterar interface, conteúdo, rotas ou sequência de atendimento.
- Alterar esquema ou dados estruturais do banco.
- Criar uma integração, endpoint público ou confirmação acionável diretamente pelo frontend.
- Modificar autenticação ou qualquer outra funcionalidade alheia ao pagamento.

## Decisions

1. **Exigir duas condições independentes para simular.** `PAYMENT_MODE=mock` e `APP_ENV=development` ou `APP_ENV=test` precisam estar explícitos. Valor ausente ou desconhecido de `APP_ENV` não habilita a simulação, preservando o caminho Asaas por padrão e falhando de forma segura em produção.
   - Alternativa considerada: habilitar mock apenas com `PAYMENT_MODE=mock`; rejeitada porque uma configuração acidental em produção poderia simular pagamentos.

2. **A aprovação permanece sob autoridade do backend.** A ação de pagamento já existente solicita a operação; somente o backend verifica autorização e os critérios de pagamento e registra a confirmação simulada. A interface recebe o resultado do servidor e segue o fluxo existente, sem endpoint ou sinalização que permita declarar aprovação no cliente.
   - Alternativa considerada: alterar o estado de pagamento localmente no frontend; rejeitada porque não é uma confirmação confiável e não pode autorizar as etapas posteriores.

3. **Reutilizar processamento pós-confirmação, sem novo modelo de dados.** A confirmação mock deve convergir para as mesmas operações existentes que processam uma confirmação válida, evitando bifurcar avaliação, estado do Prestador ou outras etapas dependentes. Apenas o estado da entidade de pagamento existente é atualizado; não se cria nem altera esquema.
   - Alternativa considerada: reproduzir separadamente as ações pós-pagamento para o mock; rejeitada por duplicar lógica e divergir do fluxo real.

4. **Manter o Asaas como caminho padrão.** Quando o mock não estiver habilitado para um ambiente de desenvolvimento/teste, a criação de checkout, a confirmação real e a validação de webhook continuam no caminho atual, sem mudanças.
   - Alternativa considerada: substituir ou adaptar o fluxo real; rejeitada por exceder o escopo e afetar produção.

**Entidades:** ler o Chamado e o estado de pagamento para aplicar as validações existentes; atualizar somente o estado da entidade de pagamento existente após simulação confirmada. Nenhuma entidade é criada ou removida; Motorista, Prestador, Tipo de Socorro, Avaliação e Localização não são alterados por esta mudança.

## Risks / Trade-offs

- [Configuração incorreta do ambiente pode habilitar simulação fora do local pretendido] → exigir tanto o modo mock explícito quanto uma identificação de ambiente não produtivo, e testar a combinação em configurações de produção.
- [Fluxo de confirmação duplicado pode deixar de executar etapas posteriores] → encaminhar a confirmação simulada pelo processamento pós-confirmação existente e cobrir a navegação/etapas com testes.
- [Teste pode acidentalmente tocar o Asaas] → verificar que a seleção mock não cria checkout nem realiza chamada externa.

## Migration Plan

Não há migração de dados ou banco. Em desenvolvimento/teste, configurar `PAYMENT_MODE=mock` e `APP_ENV=development` ou `APP_ENV=test`. Para rollback, remover ou desabilitar o modo mock; o caminho Asaas existente volta a ser usado sem alterações de dados.
