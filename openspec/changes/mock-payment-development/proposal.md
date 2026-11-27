## Why

O fluxo atual depende do Checkout e da confirmação externa do Asaas, o que impede concluir rapidamente testes do atendimento e das etapas pós-pagamento. Um modo de simulação explicitamente habilitado apenas em desenvolvimento/teste permitirá exercitar o mesmo fluxo sem alterar a confirmação real usada em produção.

## What Changes

- Adicionar um modo de pagamento simulado no backend, habilitado somente quando `PAYMENT_MODE=mock` e `APP_ENV=development` ou `APP_ENV=test` estiverem configurados.
- Quando habilitado, tratar a ação de pagamento como aprovada no backend sem abrir checkout externo e encaminhar o atendimento pelas etapas pós-pagamento existentes.
- Preservar autorização, validação e processamento no backend; a interface não poderá definir o pagamento como aprovado.
- Manter inalterado o comportamento Asaas quando o modo mock não estiver explicitamente habilitado, especialmente em produção.
- Não alterar telas, rotas, esquema do banco, autenticação ou funcionalidades fora do pagamento.

## Capabilities

### New Capabilities

- `payment-simulation`: backend-only simulated payment confirmation isolated to development/test environments.

### Modified Capabilities

Nenhuma. A especificação de pagamento após o atendimento existente permanece inalterada; a nova capacidade define somente o modo de simulação isolado.

## Impact

- Dentro do escopo de evolução da capacidade de pagamento previamente introduzida; pagamentos continuam fora do MVP originalmente descrito em `docs/project-overview.md`.
- Impacto localizado no backend Python e no acionamento existente da tela Reflex de pagamento.
- Atualiza somente o estado da entidade de pagamento existente; não modifica estrutura ou dados do banco nem os dados estruturais do Chamado, Motorista, Prestador ou Avaliação.
- Reutiliza a validação e as etapas posteriores existentes após uma confirmação válida; não introduz novo gateway, rota ou dependência.
- Reversão: remover/desabilitar `PAYMENT_MODE=mock` e voltar ao fluxo Asaas existente, sem migração ou reversão de dados.
