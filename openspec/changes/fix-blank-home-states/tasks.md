# Tasks

## 1. Retorno e montagem das Homes

- [x] 1.1 Reutilizando rotas/estado Reflex existentes, garantir que o retorno do perfil aponta para a Home do papel autenticado; verificar os destinos de Cliente e Prestador em teste do componente.
- [x] 1.2 Garantir que mapa/lista sejam inicializados ou atualizados ao retornar à Home sem duplicar listeners ou perder a sessão; validar no fluxo de montagem Reflex e com teste/mock apropriado.

## 2. Estados de conteúdo da Home

- [x] 2.1 Reutilizando a lista atual do Prestador, exibir mensagem acessível quando não houver chamados/clientes próximos, mantendo mapa e disponibilidade; testar estados disponível com lista vazia e preenchida.
- [x] 2.2 Distinguir indisponibilidade do Prestador, carregamento e falha de consulta, com feedback e ação de nova tentativa para falha; testar cada estado com dados/consultas mockados.
- [x] 2.3 Reutilizando a Home do Cliente, apresentar texto claro quando não houver chamado ativo sem ocultar "Solicitar Socorro"; testar estado sem chamado e preservar teste de chamado ativo.

## 3. Verificação integrada

- [x] 3.1 Executar testes direcionados das Homes e exportação backend Reflex; validar manualmente retorno de perfil/chamado em Cliente e Prestador e ausência de tela/área principal branca sem dados.
  - 13 testes direcionados e exportação Reflex passaram; o usuário confirmou manualmente que os fluxos autenticados de Cliente e Prestador funcionam ao retornar à Home.

## Workflow follow-up

- Arquivar a change após implementação, verificação e revisão concluídas.
