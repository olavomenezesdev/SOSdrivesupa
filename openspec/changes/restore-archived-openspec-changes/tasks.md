## 1. Inventory and restore

- [x] 1.1 (reutilizar a estrutura OpenSpec existente) Inventariar os pacotes em
  `openspec/changes/archive/`: 10 concluídos, 2 sem confirmação por ausência de
  `tasks.md`, 1 incompleto e nenhum conflito de nome.
- [x] 1.2 (reutilizar os artefatos existentes; sem editar o conteúdo) Mover
  os 10 pacotes concluídos e sem colisões de `openspec/changes/archive/` para
  `openspec/changes/`, preservando seus nomes e arquivos.
- [x] 1.3 (operação de arquivos existente) Remover
  `openspec/changes/archive/` somente se estiver vazia; preservar e reportar os
  3 pacotes cuja conclusão não foi confirmada. O diretório permanece porque
  esses pacotes ainda estão nele.

## 2. Regra operacional

- [x] 2.1 (documentação existente) Atualizar `AGENTS.md` para que mudanças
  concluídas permaneçam em `openspec/changes/` e não sejam movidas para
  `openspec/changes/archive/` ao finalizar.

## 3. Verificação

- [x] 3.1 (verificação da estrutura existente) Confirmar que os 10 pacotes
  elegíveis foram restaurados sem perda ou alteração de conteúdo, que os 3
  pacotes incompletos/não confirmados continuam arquivados e que nenhum arquivo
  foi sobrescrito; os hashes dos arquivos antes/depois da movimentação foram
  comparados.
- [x] 3.2 (validação OpenSpec) Executar a validação dos pacotes afetados se a
  CLI estiver disponível; se não houver pacotes arquivados, registrar que a
  migração não exigiu movimentações. Oito pacotes validaram; `2026-10-21-migrate-streamlit-to-reflex`
  e `2026-10-21-profile-and-vehicles-ui` têm erros de estrutura delta
  preexistentes, preservados sem edição.
