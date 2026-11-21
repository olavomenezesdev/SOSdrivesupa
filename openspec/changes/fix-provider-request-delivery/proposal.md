## Why

Há chamados `pending` sem prestador no Supabase, mas a Área do Prestador continua exibindo zero solicitações, impedindo que sejam aceitos. A RPC de listagem retornou chamados em um teste autorizado e a página atual não mostra erro de consulta; é necessário tornar confiáveis e verificáveis a carga inicial e o polling da fila.

## What Changes

- Garantir que a fila de solicitações pendentes seja carregada ao entrar na Área do Prestador e continue atualizada enquanto a tela estiver aberta.
- Expor falhas de inicialização ou atualização com mensagem e ação de nova tentativa, sem apresentar uma falha como lista vazia.
- Registrar diagnósticos seguros e úteis para distinguir falha de evento/polling, autorização e consulta Supabase.
- Preservar a aceitação de chamados, os cards de atendimentos ativos e os fluxos existentes de cliente e prestador.
- Não alterar schema, políticas RLS ou migrations sem evidência de que sejam a causa.

## Capabilities

### New Capabilities

- `provider-request-queue`: carregamento, atualização e feedback da fila de chamados disponíveis na Área do Prestador.

### Modified Capabilities

Nenhuma.

## Impact

- **MVP:** Sim; corrige o recebimento de chamados no fluxo essencial do Prestador.
- **Código previsto:** estado e eventos Reflex em `sosdrive.py`, consultas/wrappers em `supabase_backend.py` somente se a investigação apontar para eles, e testes focados.
- **Entidades:** Chamado e Prestador; Localização permanece somente como dado de ordenação/exibição. Não há mudança planejada em dados persistidos.
- **Reuso:** corrige a montagem/polling e as consultas atuais; não introduz framework ou dependência.
- **Autorização e dados:** manter verificações no backend e as políticas existentes; nenhuma alteração de schema/RLS planejada.
- **Verificação:** testes de inicialização, polling, falha/retry e preservação de chamados ativos, além de validação Reflex e conferência manual com sessões de cliente/prestador.
- **Rollback:** reverter os ajustes de estado/eventos e testes. Não há migração nem alteração persistente de dados.
