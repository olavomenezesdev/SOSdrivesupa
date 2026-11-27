## Purpose

Define um modo de pagamento simulado para concluir testes do fluxo de pagamento sem checkout ou confirmação externa, sem permitir aprovação simulada em produção.

## ADDED Requirements

### Requirement: Restringir a simulação ao modo de desenvolvimento
O sistema MUST simular a aprovação somente quando `PAYMENT_MODE=mock` e `APP_ENV=development` ou `APP_ENV=test` estiverem explicitamente configurados. Um valor de `APP_ENV` ausente ou desconhecido MUST NOT habilitar a simulação. Em produção, ou quando essas condições não forem simultaneamente atendidas, o sistema MUST manter o fluxo de pagamento real do Asaas.

#### Scenario: Simulação explicitamente habilitada em desenvolvimento
- **WHEN** o Motorista autorizado aciona o pagamento com `PAYMENT_MODE=mock` e `APP_ENV=development` ou `APP_ENV=test`
- **THEN** o backend confirma a simulação sem abrir um checkout externo ou depender de uma notificação do Asaas

#### Scenario: Modo mock configurado em produção
- **WHEN** o Motorista aciona o pagamento em produção, mesmo que `PAYMENT_MODE=mock` esteja configurado
- **THEN** o sistema não simula aprovação e mantém a criação e confirmação real pelo Asaas

#### Scenario: Modo mock não explicitamente habilitado
- **WHEN** o Motorista aciona o pagamento e o modo mock não está explicitamente configurado
- **THEN** o sistema mantém o fluxo de pagamento real do Asaas

#### Scenario: Ambiente não identificado
- **WHEN** `PAYMENT_MODE=mock` está configurado, mas `APP_ENV` está ausente ou contém um valor desconhecido
- **THEN** o sistema não simula aprovação e mantém o fluxo de pagamento real do Asaas

### Requirement: Aprovar a simulação exclusivamente no backend
A interface MUST NOT aprovar ou marcar um pagamento como confirmado por conta própria. O backend MUST validar a identidade e autorização do Motorista, aplicar as validações de pagamento existentes e atualizar o estado confirmado da simulação antes de devolver o resultado à interface.

#### Scenario: Interface solicita o pagamento simulado
- **WHEN** o Motorista autorizado aciona a ação de pagamento no modo mock habilitado
- **THEN** a interface recebe confirmação somente após o backend validar e atualizar o estado do pagamento

#### Scenario: Tentativa de aprovação direta pela interface
- **WHEN** uma solicitação da interface tenta declarar um pagamento aprovado sem passar pela validação do backend
- **THEN** o sistema não aceita a confirmação nem avança o fluxo pós-pagamento

### Requirement: Reutilizar o fluxo posterior à confirmação
Após confirmar uma simulação válida, o sistema MUST executar as mesmas etapas pós-pagamento existentes para uma confirmação válida do Asaas. A tela, o resumo do atendimento e os dados exibidos antes do pagamento MUST permanecer inalterados.

#### Scenario: Pagamento simulado confirmado
- **WHEN** o backend confirma um pagamento válido no modo mock habilitado
- **THEN** o sistema atualiza o estado do pagamento e encaminha o Motorista para a próxima etapa existente após confirmação, sem exigir checkout externo ou espera por webhook

#### Scenario: Asaas real continua sendo usado fora da simulação
- **WHEN** o pagamento é processado sem satisfazer as condições do modo mock
- **THEN** o sistema preserva o fluxo existente de checkout, confirmação do Asaas e processamento de webhook
