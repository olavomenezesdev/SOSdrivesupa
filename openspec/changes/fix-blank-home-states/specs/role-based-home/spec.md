# Spec Delta

## Purpose

Define como as Homes do Cliente e do Prestador recuperam conteúdo após navegação e comunicam estados de carregamento, falha ou ausência de chamados, para que áreas sem dados nunca pareçam uma tela quebrada.

## ADDED Requirements

### Requirement: Home recupera conteúdo ao retornar da navegação
O sistema MUST renderizar novamente o conteúdo correto da Home correspondente ao papel autenticado quando o usuário voltar de um chamado ou do perfil.

#### Scenario: Retorno do perfil
- **GIVEN** um Cliente ou Prestador autenticado em seu perfil
- **WHEN** seleciona a ação para voltar à Home
- **THEN** o sistema abre a Home do papel correspondente e exibe seu conteúdo sem uma área principal em branco

#### Scenario: Retorno de um chamado
- **GIVEN** um Cliente ou Prestador que saiu da Home para acompanhar ou atender um chamado
- **WHEN** retorna à Home
- **THEN** o sistema renderiza os controles e o conteúdo da Home sem exigir recarga manual da página

### Requirement: Home do Prestador comunica ausência de chamados
A Home do Prestador MUST exibir um estado vazio explicativo quando não houver chamados próximos disponíveis, sem remover o mapa ou os controles de disponibilidade.

#### Scenario: Nenhum chamado disponível
- **GIVEN** que o Prestador está disponível
- **WHEN** não há chamados próximos para exibir
- **THEN** a lista mostra uma mensagem informando que não há chamados ou clientes próximos no momento

#### Scenario: Prestador indisponível
- **GIVEN** que o Prestador está indisponível
- **WHEN** visualiza a lista de chamados
- **THEN** a Home explica que ele está indisponível para novos chamados e mantém acessível o controle para alterar sua disponibilidade

### Requirement: Home do Cliente comunica ausência de chamado ativo
A Home do Cliente MUST explicar quando não há chamado ativo e manter acessível a ação para solicitar assistência.

#### Scenario: Cliente sem chamado ativo
- **GIVEN** que não existe chamado ativo para o Cliente
- **WHEN** visualiza sua Home
- **THEN** a Home informa que não há chamado em andamento e mantém visível a ação para solicitar socorro

### Requirement: Home diferencia carregamento e falha de conteúdo
O sistema MUST informar estados de carregamento ou falha ao buscar conteúdo das Homes, em vez de deixar a área de conteúdo vazia.

#### Scenario: Conteúdo carregando
- **GIVEN** que a Home está buscando dados necessários para apresentar chamados
- **WHEN** a busca ainda não foi concluída
- **THEN** a área correspondente apresenta um indicador ou mensagem de carregamento

#### Scenario: Falha ao carregar conteúdo
- **GIVEN** uma falha ao buscar dados necessários para a Home
- **WHEN** a Home termina a tentativa de carregamento
- **THEN** apresenta uma mensagem compreensível e uma ação apropriada para tentar novamente, sem apagar o restante da Home
