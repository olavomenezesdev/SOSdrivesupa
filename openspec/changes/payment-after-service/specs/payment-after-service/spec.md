# Spec Delta

## Purpose

Permite que o Motorista revise e pague um atendimento concluído por um Prestador somente por cartão de crédito via Checkout hospedado do Asaas, mantendo autorização e valor vinculados ao Chamado.

## ADDED Requirements

### Requirement: Abrir pagamento após conclusão
O sistema MUST apresentar a tela de pagamento somente para um Chamado concluído pertencente ao Motorista autenticado.

#### Scenario: Chamado concluído do proprietário
- **WHEN** o Chamado muda para `completed`
- **THEN** o Motorista é encaminhado ao resumo e às formas de pagamento do atendimento

#### Scenario: Usuário abre pagamento de outro Chamado
- **WHEN** o usuário informa ou tenta acessar um Chamado que não lhe pertence
- **THEN** o sistema impede a exibição dos dados e da cobrança

#### Scenario: Chamado ainda não concluído
- **WHEN** o usuário abre a tela de pagamento antes do status `completed`
- **THEN** o sistema mantém o fluxo no acompanhamento do Chamado e não cria cobrança

### Requirement: Exibir resumo do atendimento
A tela MUST apresentar os dados necessários para confirmar o valor e identificar o atendimento.

#### Scenario: Resumo disponível
- **WHEN** o usuário abre o pagamento de um Chamado válido
- **THEN** o sistema mostra serviço, Prestador, veículo, distância, data, localização, valor do serviço, taxa e total

### Requirement: Selecionar forma de pagamento
O sistema MUST oferecer somente cartão de crédito por meio de Checkout hospedado pelo Asaas.

#### Scenario: Cartão selecionado
- **WHEN** o usuário inicia o pagamento do atendimento
- **THEN** o sistema cria uma sessão segura do Checkout Asaas limitada a cartão e os dados do cartão são coletados diretamente pelo Asaas, sem passar pelo SOS Drive

### Requirement: Bloquear saída do prestador até confirmação
O Prestador MUST permanecer na tela de aguardando pagamento depois de concluir o atendimento até o Asaas confirmar a cobrança por webhook autorizado.

#### Scenario: Atendimento concluído sem pagamento
- **WHEN** o prestador conclui o Chamado e o Motorista ainda não confirmou o pagamento
- **THEN** o sistema mantém o prestador em uma tela de aguardando pagamento e impede voltar para novos chamados

#### Scenario: Pagamento confirmado
- **WHEN** o webhook autorizado do Asaas confirma o pagamento do cartão
- **THEN** o sistema libera o prestador para avaliações e deixa o fluxo disponível para voltar à Home

### Requirement: Avaliar após pagamento confirmado
Motorista e Prestador MUST poder avaliar o outro participante somente após o pagamento confirmado.

#### Scenario: Avaliação do motorista
- **WHEN** o pagamento é confirmado
- **THEN** o Motorista pode atribuir nota e comentário ao Prestador em uma tela pós-pagamento

#### Scenario: Avaliação do prestador
- **WHEN** o pagamento é confirmado
- **THEN** o Prestador pode atribuir nota e comentário ao Motorista em uma tela pós-pagamento usando o identificador do Chamado aceito, mesmo que `request_id` não esteja definido no estado

#### Scenario: Uma avaliação por participante
- **WHEN** uma das partes tenta avaliar o mesmo Chamado novamente
- **THEN** o sistema mostra a avaliação já registrada e não permite duplicação

### Requirement: Exibir avaliações no perfil
As avaliações recebidas MUST ser exibidas no perfil público ou autenticado do participante correspondente.

#### Scenario: Perfil do prestador
- **WHEN** um usuário abre o perfil do Prestador avaliado
- **THEN** o sistema mostra nota média e avaliações recebidas

#### Scenario: Perfil do motorista
- **WHEN** o usuário autorizado abre o perfil do Motorista avaliado
- **THEN** o sistema mostra nota média e avaliações recebidas

### Requirement: Confirmar cobrança antes do pagamento
O sistema MUST criar a cobrança no backend usando o total autorizado do Chamado e não confiar no valor enviado pela interface.

#### Scenario: Valor confirmado pelo servidor
- **WHEN** o usuário confirma o pagamento
- **THEN** o backend obtém o valor persistido do Chamado, cria a cobrança e retorna apenas os dados necessários ao usuário

#### Scenario: Tentativa com valor divergente
- **WHEN** a interface envia um valor diferente do valor persistido
- **THEN** o sistema ignora o valor enviado e utiliza ou rejeita conforme o estado seguro do Chamado

### Requirement: Reportar estado da cobrança
O sistema MUST informar o estado real da cobrança e MUST NOT confirmar pagamento sem confirmação do gateway ou webhook autorizado.

#### Scenario: Cobrança pendente
- **WHEN** o gateway cria a cobrança de cartão aguardando pagamento
- **THEN** a tela mostra o estado pendente e atualiza quando houver confirmação

#### Scenario: Pagamento confirmado
- **WHEN** o Checkout Asaas confirma o pagamento por evento autorizado
- **THEN** o sistema registra o pagamento confirmado e informa sucesso ao Motorista

#### Scenario: Pagamento recusado ou expirado
- **WHEN** o gateway recusa ou expira a cobrança
- **THEN** o sistema informa a falha em português e permite nova tentativa

### Requirement: Registrar e exibir ganhos confirmados do Prestador
O sistema MUST registrar no saldo interno do Prestador o valor total persistido do serviço somente após a confirmação oficial do pagamento. O registro MUST ser único por Chamado e MUST NOT representar transferência bancária, saque ou repasse automático.

#### Scenario: Pagamento confirmado credita o Prestador
- **WHEN** o backend confirma o pagamento por webhook autorizado ou reconciliação autenticada
- **THEN** o sistema registra uma única vez o valor total persistido do serviço como ganho do Prestador e atualiza o saldo exibido na conta do Prestador

#### Scenario: Confirmação repetida não duplica o saldo
- **WHEN** o mesmo pagamento confirmado é processado novamente por webhook duplicado ou nova reconciliação
- **THEN** o sistema mantém um único lançamento para o Chamado e não aumenta o saldo novamente

#### Scenario: Pagamento não confirmado não credita saldo
- **WHEN** o pagamento está pendente, recusado, expirado ou cancelado
- **THEN** o sistema não cria lançamento de ganho nem inclui o valor no saldo do Prestador

#### Scenario: Saldo consultado pelo Prestador
- **WHEN** o Prestador autenticado consulta sua conta
- **THEN** o sistema exibe a soma dos ganhos confirmados vinculados a ele e não permite consultar ganhos de outro Prestador

#### Scenario: Saldo interno sem liquidação automática
- **WHEN** um pagamento é confirmado e o saldo interno é atualizado
- **THEN** o sistema não declara que houve transferência, saque ou crédito bancário ao Prestador

### Requirement: Retornar o Motorista à Home após avaliação
Depois da confirmação do pagamento, o Motorista MUST poder concluir ou reconhecer a avaliação do atendimento e retornar à Home do cliente.

#### Scenario: Avaliação enviada
- **WHEN** o Motorista envia a avaliação do Chamado pago
- **THEN** o sistema registra a avaliação e retorna o Motorista para `/home_client`

#### Scenario: Avaliação já registrada
- **WHEN** o Motorista abre novamente a avaliação de um Chamado pago cuja avaliação já existe
- **THEN** o sistema informa que ela já foi registrada e oferece o retorno para `/home_client`

### Requirement: Reconciliar pagamento pendente com o Asaas
Quando um pagamento de cartão continuar pendente, o sistema MUST poder consultar o estado da cobrança diretamente na API autenticada do Asaas usando o identificador do Checkout persistido no backend. A reconciliação MUST confirmar somente uma cobrança única que corresponda ao Checkout e ao valor persistido do Chamado e cujo estado no Asaas seja `CONFIRMED` ou `RECEIVED`.

#### Scenario: Asaas confirma cobrança durante atualização manual
- **WHEN** o Motorista atualiza o status de um pagamento pendente e o Asaas retorna uma cobrança `CONFIRMED` ou `RECEIVED` vinculada ao Checkout e valor registrados
- **THEN** o backend persiste a confirmação e a interface segue para a avaliação sem depender da entrega do webhook

#### Scenario: Asaas ainda não confirmou ou não encontra cobrança
- **WHEN** a consulta autenticada não retorna cobrança correspondente ou a cobrança permanece pendente
- **THEN** o sistema mantém o status pendente e não libera avaliações

#### Scenario: Resultado não corresponde ao Checkout ou valor persistido
- **WHEN** a consulta retorna cobranças ambíguas ou com Checkout ou valor divergente
- **THEN** o backend não altera o status e registra uma falha segura sem expor dados financeiros ou credenciais
