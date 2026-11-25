# Logout Specification

## Purpose

Define how an authenticated user ends their current SOS Drive session from the profile page and returns to the login screen without changing persisted profile or service data.

## Requirements

### Requirement: Usuário pode sair pela página de perfil

O sistema MUST oferecer uma ação de saída visível na página de perfil para usuários autenticados, independentemente do papel de Motorista ou Prestador.

#### Scenario: Ação de saída disponível no perfil
- **GIVEN** um Motorista ou Prestador autenticado está na página de perfil
- **WHEN** a página é exibida
- **THEN** o sistema apresenta a ação “Sair” separada da navegação “Voltar”

### Requirement: Saída encerra a sessão atual

Quando o usuário acionar a saída, o sistema MUST limpar os tokens e os dados de usuário mantidos na sessão Reflex atual e MUST redirecionar o usuário para `/login`.

#### Scenario: Usuário encerra a sessão pelo perfil
- **GIVEN** um usuário está autenticado na página de perfil
- **WHEN** o usuário aciona “Sair”
- **THEN** o estado autenticado da sessão atual é limpo e o navegador é redirecionado para `/login`

#### Scenario: Perfil não é alterado ao sair
- **GIVEN** um usuário autenticado possui dados de perfil e veículos cadastrados
- **WHEN** o usuário aciona “Sair”
- **THEN** o sistema encerra apenas a sessão e não altera nem remove dados persistidos do perfil ou dos veículos

### Requirement: Rotas protegidas exigem autenticação após a saída

Depois da saída, o sistema MUST tratar a sessão atual como não autenticada e MUST direcionar tentativas de acesso a páginas protegidas para `/login`.

#### Scenario: Usuário tenta reabrir página protegida após sair
- **GIVEN** o usuário encerrou a sessão atual
- **WHEN** tenta acessar uma rota protegida sem autenticar novamente
- **THEN** o sistema redireciona o usuário para `/login`
