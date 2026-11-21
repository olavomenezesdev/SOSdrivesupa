## Context

Consulte `proposal.md` e `specs/provider-request-queue/spec.md`. A rota `/home_provider` consulta pendentes pela RPC autorizada existente, combina-os com chamados ativos e já possui eventos distintos para carregamento pontual e polling de fundo. Atualmente, o `on_mount` da página inicia apenas o polling de fundo; o `on_mount` de mapa em `provider_dashboard` pertence a outra rota (`/provider`) e não deve ser removido como se fosse uma duplicação em `/home_provider`. A chamada da RPC retornou pendentes em teste autorizado, mas isso não comprova o resultado com a sessão real do navegador; a página observada continua em zero, embora o WebSocket esteja ativo e não haja falha JavaScript/rede visível no navegador.

## Goals / Non-Goals

**Goals:**
- Tornar observável cada etapa entre montagem da Área do Prestador, obtenção da identidade autenticada, retorno do backend e atualização do State.
- Garantir uma primeira carga explícita e manter um único ciclo de polling, com erros e retry visíveis.
- Evitar que dados de localização incompletos em um Chamado impeçam a exibição dos demais chamados retornados.
- Preservar a fila autorizada atual, os chamados ativos e seus badges, a aceitação e as demais telas.

**Non-Goals:**
- Alterar status, regras de aceitação, disponibilidade, especialidades, schema, políticas RLS ou migrations sem evidência obtida com a sessão real.
- Refazer o layout ou introduzir serviços/dependências novos.

## Decisions

1. **Manter a RPC autorizada existente como fonte dos pendentes**
   - Fazer primeiro uma reprodução com a sessão real e registrar, sem dados pessoais, se o evento de montagem iniciou, se há identidade autenticada, a contagem retornada e a contagem aplicada ao State.
   - Corrigir o ponto comprovado do fluxo; preservar `list_pending_service_requests` e suas regras. Só investigar alteração SQL/RLS se a RPC retornar zero ou negar acesso com essa sessão apesar de haver Chamados elegíveis.
   - Alternativa: substituir a RPC por leitura direta da tabela. Rejeitada porque a policy de leitura direta protege Chamados não atribuídos e a RPC já é o caminho autorizado para a fila.

2. **Separar a carga inicial do polling recorrente**
   - Na rota `/home_provider`, reutilizar o carregamento pontual existente ao montar a página e iniciar um único polling de fundo protegido pela guarda atual. O primeiro ciclo periódico não deve competir com a carga inicial; manter a chamada de polling da rota `/provider` independente.
   - Manter o intervalo de polling atual e refletir falhas no estado de erro/retry, sem converter uma falha em lista vazia.
   - Alternativa: depender somente de um loop de fundo para a primeira carga. Rejeitada porque a lista e o erro inicial ficam acoplados a uma tarefa longa e dificultam distinguir uma fila vazia de uma montagem que não iniciou a consulta.

3. **Mapear registros sem coordenadas sem descartar a fila**
   - Tratar localização como opcional para a exibição do Chamado: quando ausente/inválida, preservar acesso a detalhes e aceitação e mostrar distância indisponível. Isolar o registro inválido para que não descarte os demais.
   - Alternativa: lançar erro para a lista inteira se uma coordenada estiver ausente. Rejeitada porque uma informação geográfica incompleta não deve ocultar Chamados elegíveis.

4. **Diagnósticos seguros e verificáveis**
   - Registrar apenas etapa, contagens, status HTTP/categoria de erro e resultado de atualização do State. Nunca registrar token, nome/contato do cliente, identificadores pessoais ou coordenadas.
   - Cobrir a inicialização, respostas vazias, erro/retry, dados de localização incompletos e coexistência de Chamados pendentes/ativos com testes focados; validar a montagem com `reflex compile` e uma verificação manual em sessões distintas.

## Risks / Trade-offs

- [O evento de montagem e o polling podem iniciar em paralelo] → centralizar a inicialização e cobrir a guarda contra duplicação com teste.
- [A sessão real pode receber erro de autorização ou retorno diferente da consulta simulada] → registrar categoria/status sem dados sensíveis e conferir a definição implantada da RPC antes de propor qualquer ajuste SQL/RLS.
- [A distância deixar de ser calculada para um registro inválido] → manter o Chamado disponível e representar apenas a distância como indisponível.

## Migration Plan

Nenhuma migração de dados. Alterar somente os eventos/estado Python e os testes necessários. Reverter esses ajustes restaura o ciclo de polling anterior; não há alterações persistentes a desfazer.

## Open Questions

- A contagem da RPC com o token real do Prestador e a etapa exata onde a lista deixa de chegar ao State serão confirmadas durante a implementação. Se essa evidência mostrar diferença na função implantada, comparar a definição e as permissões no Supabase antes de decidir qualquer SQL.
