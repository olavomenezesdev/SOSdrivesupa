## Why

O repositório já migrou a aplicação para Supabase, mas ainda pode conter arquivos redundantes, backups, código e ferramentas legadas do Xano que confundem manutenção e testes. Uma auditoria baseada em referências explícitas permitirá remover somente resíduos comprovadamente inativos sem afetar os fluxos atuais nem a configuração ou estrutura do Supabase.

## What Changes

- Inventariar referências e dependências no repositório antes de cada exclusão, incluindo imports, rotas, configuração Reflex, testes, scripts, assets e documentação.
- Remover a pasta `xano/`, o script `xano_smoke_test.sh`, testes de integração exclusivos do Xano e código/imports/fallbacks Xano comprovadamente mortos.
- Remover somente duplicatas, backups, scripts e assets com zero referências ativas confirmadas; preservar arquivos duvidosos e históricos para decisão do usuário.
- Manter inalterados banco, migrations, manifest, RLS, `supabase_config.py`, lógica funcional de `supabase_backend.py`, dependências e funcionalidades atuais.
- Executar testes, verificações de import/sintaxe e validação de inicialização Reflex; registrar arquivos removidos, mantidos e resultados.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

Nenhuma. Esta é uma limpeza/refatoração de repositório sem mudança de comportamento observável.

## Impact

- Escopo de manutenção do MVP; não altera entidades ou regras de Motorista, Prestador, Tipo de Socorro, Chamado, Avaliação ou Localização.
- Pode remover arquivos e trechos de código Python de legado após comprovar ausência de uso; não introduz tecnologia ou dependência.
- `sosdrive.py`, `styles.py`, testes e inventário de arquivos podem ser afetados. `supabase_backend.py`, `supabase_config.py`, `supabase/`, arquivos essenciais e fluxos atuais estão fora do escopo de edição.
- Documentação histórica OpenSpec sobre migração ou Xano será preservada e listada como dúvida, não apagada automaticamente.
- Nenhum dado persistido será alterado; rollback consiste em restaurar arquivos removidos a partir do controle de versão.
