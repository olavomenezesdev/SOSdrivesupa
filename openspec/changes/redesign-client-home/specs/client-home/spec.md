# Spec Delta

## Purpose

Define a Home do Cliente como uma experiência visual clara para localizar
prestadores, escolher um tipo de socorro e solicitar atendimento sem alterar
as operações existentes do produto.

## ADDED Requirements

### Requirement: Home do Cliente apresenta o mapa e a localização
The system MUST present the client's map area, current location indicator,
address control, and nearby professional availability in the primary Home
layout.

#### Scenario: Home carregada com localização disponível
- **WHEN** o cliente abre a Home com uma localização válida
- **THEN** a interface mostra o mapa, a posição do cliente, o endereço atual
  e o indicador de profissionais disponíveis

#### Scenario: Localização indisponível
- **WHEN** a localização do cliente não está disponível
- **THEN** a interface mantém a Home utilizável com o mapa em sua posição
  padrão e preserva o feedback já existente sobre a localização

### Requirement: Home do Cliente organiza a escolha de socorro
The system MUST display the available service types as selectable cards with
their existing labels, icons, and arrival estimates.

#### Scenario: Seleção de um serviço
- **WHEN** o cliente seleciona um cartão de serviço
- **THEN** o cartão fica visualmente selecionado e a ação principal identifica
  o serviço escolhido

#### Scenario: Troca de serviço selecionado
- **WHEN** o cliente seleciona outro cartão
- **THEN** somente o novo serviço fica selecionado e os dados da solicitação
  continuam usando a seleção atual

### Requirement: Ações da Home preservam o comportamento existente
The system MUST keep the existing request, vehicle, messaging, loading, error,
authentication, and navigation behavior while changing only the Home
presentation.

#### Scenario: Solicitação de socorro
- **WHEN** o cliente aciona a ação principal com dados válidos
- **THEN** o sistema executa o mesmo fluxo atual de criação e acompanhamento
  do chamado

#### Scenario: Mensagens do chamado
- **WHEN** o cliente aciona mensagens na Home
- **THEN** o sistema abre o mesmo painel e usa a mesma sincronização existente

#### Scenario: Estado de carregamento ou erro
- **WHEN** a Home está carregando dados ou encontra um erro
- **THEN** os estados e ações de recuperação existentes permanecem disponíveis
  em uma apresentação visual consistente com a nova Home
