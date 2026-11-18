# Proposal

## Why

A landing atual não corresponde ao PNG de referência compartilhado, que apresenta uma composição mais clara e direta para explicar a assistência SOS Drive. A página inicial deve reproduzir essa identidade visual no lugar da atual, mantendo navegação e ações utilizáveis em desktop e celular.

## What Changes

- Substituir a apresentação da rota `/` por uma reconstrução responsiva do layout do PNG, em vez de renderizar a imagem como fundo estático.
- Reproduzir a hierarquia, textos, cores, espaçamentos e composição da referência: navegação superior, hero em duas colunas com chamadas para ação e mapa ilustrativo, explicação em três etapas, cartões de serviços e faixa final de pedido de ajuda.
- Ligar navegação, cadastro, login, pedido de assistência e consulta de prestadores às rotas/fluxos existentes, sem alterar seus comportamentos de autenticação ou atendimento.
- Preservar acessibilidade, legibilidade e adaptação a telas estreitas; substituir o mapa ilustrativo por uma composição local/Reflex que não dependa de serviço de mapa ou conta de usuário.

## Capabilities

### New Capabilities

- `web/landing-page-experience`: apresentação e navegação da landing pública do SOS Drive, alinhadas à imagem de referência e com ações funcionais.

### Modified Capabilities

Nenhuma. A listagem atual de specs não contém uma capability de landing page ativa; a mudança anterior de hero está em alterações OpenSpec antigas, sem spec principal correspondente.

## Impact

- **Dentro do MVP:** Sim; substitui a página pública de apresentação existente sem ampliar o escopo do produto.
- **Entidades:** nenhuma entidade de domínio é criada, lida, atualizada ou removida nesta página; os botões encaminham aos fluxos já existentes de Motorista/Cliente e Prestador.
- **Reuso:** substitui o componente atualmente servido na rota `/`, reutilizando tokens de `styles.py`, assets locais e as rotas já registradas em Reflex.
- **Tecnologia/API/dados:** somente Python + Reflex e CSS/assets locais; sem novo framework, endpoint, dependência ou alteração de dados/autorização.
- **Verificação:** comparar desktop e mobile com o PNG, validar navegação/CTAs e executar testes de renderização e exportação Reflex.
- **Rollback:** restaurar o componente anterior da landing na rota `/`; não há migração persistente.
