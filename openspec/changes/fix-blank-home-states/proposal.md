# Proposal

## Why

Ao voltar de um chamado ou do perfil, as Homes do Motorista/Cliente e do Prestador podem aparecer em branco, sem recuperar seu conteúdo. Quando não há chamados/clientes disponíveis, a ausência de itens também não explica se a tela está vazia ou falhou ao carregar.

## What Changes

- Corrigir o ciclo de retorno/navegação para que as Homes de Cliente e Prestador voltem a renderizar seu conteúdo após sair de perfil ou de um chamado.
- Exibir estados de carregamento, erro e vazio com mensagens claras nas Homes, sem deixar áreas de conteúdo totalmente brancas.
- Na Home do Prestador, informar explicitamente quando não houver chamados/clientes disponíveis.
- Na Home do Cliente, orientar o usuário quando ainda não houver chamado ativo, mantendo acessíveis as ações para solicitar assistência.
- Preservar os dados e as ações já existentes quando houver conteúdo disponível.

## Capabilities

### New Capabilities

- `role-based-home`: comportamento das Homes de Cliente e Prestador, incluindo recuperação de navegação e apresentação de estados sem conteúdo.

### Modified Capabilities

Nenhuma. A listagem atual de specs não contém uma capability de Home a ser modificada; propostas antigas de Home estão arquivadas e não possuem spec principal ativa.

## Impact

- **Dentro do MVP:** Sim; melhora as jornadas existentes para Motoristas/Clientes e Prestadores.
- **Entidades:** apresenta dados existentes de Motorista/Cliente, Prestador, Chamado e Localização; não muda regras nem dados dessas entidades.
- **Reuso:** reutiliza rotas, estados, chamadas de dados e estilos atuais em Python/Reflex; não adiciona framework ou dependência.
- **API/dados/autorização:** sem alterações planejadas em schema, API ou permissões. As regras atuais de acesso continuam no backend.
- **Verificação:** testes para navegação de retorno e estados vazio/carregando/erro com mocks, além de validação/export Reflex.
- **Rollback:** reverter os ajustes de navegação e apresentação dos estados; não há migração nem alteração persistente de dados.
