# Design

## Context

Veja a motivação em `proposal.md` e o contrato comportamental em `specs/role-based-home/spec.md`. As rotas protegidas já restauram a sessão antes de renderizar a página. A Home do Prestador monta o mapa e consulta chamados ao entrar; a lista atual não apresenta uma mensagem própria quando está vazia. A Home do Cliente exibe uma ação padrão quando não há chamado ativo.

## Goals / Non-Goals

**Goals:**
- Reutilizar as rotas e os estados de Home atuais e garantir que o conteúdo e os componentes de mapa/lista sejam reinicializados com segurança quando o usuário retorna à rota.
- Distinguir ausência legítima de chamados de carregamento e falha de consulta; não substituir um estado pelo outro.
- Manter a identidade e disponibilidade do usuário autenticado ao retornar, sem exigir refresh do navegador.

**Non-Goals:**
- Alterar o ciclo de vida ou persistência de Chamado, criar um histórico novo, mudar regras de disponibilidade ou ajustar o mapa/geolocalização fora do necessário para restaurar a Home.
- Mudar políticas de autorização, schema do banco, API ou configuração externa.

## Decisions

1. **Reutilizar as páginas Home e seu ciclo de montagem**
   - Investigar o retorno de `/profile`, `/customer` e telas do Prestador para as rotas Home já usadas; corrigir o evento/estado ou a remontagem de componentes existente, sem duplicar páginas.
   - Reaproveitar a validação de sessão protegida e garantir que a navegação de retorno use a Home correspondente ao papel autenticado.
   - Alternativa: forçar reload de página ou redirecionar para uma rota genérica. Rejeitada por mascarar o problema de renderização e poder perder o estado de sessão.

2. **Representar explicitamente os estados da lista do Prestador**
   - Condicionar o conteúdo existente a carregamento, erro, lista vazia e lista preenchida. A lista vazia deve informar que não há chamados/clientes próximos no momento, mantendo mapa e controle de disponibilidade visíveis.
   - A indisponibilidade permanece distinta de lista vazia; preservar o controle atual de disponibilidade.
   - Alternativa: renderizar lista vazia sem feedback ou misturar indisponibilidade com falta de chamados. Rejeitada por deixar a área visualmente sem conteúdo e não explicar o motivo.

3. **Preservar a ação principal do Cliente**
   - Manter a ação Solicitar Socorro visível quando não houver chamado ativo e comunicar esse estado em texto no local de status atual.
   - Alternativa: ocultar a ação até carregar algum chamado. Rejeitada porque o Cliente sem chamado precisa conseguir iniciar a jornada.

4. **Autorização e dados**
   - A UI exibirá somente os dados que os estados existentes já recebem; toda autorização e filtragem continuam nas operações backend/Supabase e nas políticas existentes. Nenhuma entidade é criada, removida ou atualizada: Chamado e Localização podem ser lidos; Motorista/Cliente e Prestador são identificados pela sessão atual.

## Risks / Trade-offs

- [A desmontagem e remontagem de mapa Leaflet pode manter um mapa antigo ou não calcular dimensões] → tornar a inicialização idempotente e invalidar/recalcular o mapa somente quando a Home for montada novamente; cobrir o ciclo no teste e validar export Reflex.
- [Falha de consulta pode ser confundida com lista vazia] → manter status de carregamento/erro separado dos dados e oferecer retry explícito apenas para falha.
- [A navegação pode expor estados de uma sessão anterior] → restaurar/validar sessão antes de renderizar, sem copiar dados entre papéis ou remover as regras atuais de autorização.

## Migration Plan

Nenhuma migração de dados. Implementar mudanças nas páginas e estado existentes, executar testes unitários com consultas mockadas e export Reflex. Rollback: reverter os ajustes de remontagem e os componentes de estado vazio/erro.

## Open Questions

Nenhuma.
