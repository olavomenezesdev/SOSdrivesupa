## Por que

As mudanças do OpenSpec que já foram concluídas e arquivadas precisam continuar
disponíveis em `openspec/changes/`, junto às demais mudanças do projeto. No
estado atual, os pacotes arquivados estão em
`openspec/changes/archive/`. O inventário encontrou 13 pacotes: 10 com todas as
tarefas concluídas, 2 sem confirmação de conclusão e 1 com tarefas pendentes.
Não há colisões de nomes em `openspec/changes/`.

## O que muda

- Restaurar para `openspec/changes/` cada pacote de mudança concluído encontrado
  em `openspec/changes/archive/`.
- Registrar no fluxo operacional do projeto que mudanças concluídas devem
  permanecer em `openspec/changes/`, sem serem arquivadas ao finalizar.
- Preservar os arquivos e o conteúdo de cada pacote sem alterar seus artefatos.
- Remover a pasta `openspec/changes/archive/` somente quando estiver vazia após a
  restauração.
- Interromper a restauração de qualquer pacote com conflito de nome ou conteúdo,
  sem sobrescrever nem descartar arquivos.
- Verificar e documentar o resultado; se não houver arquivo arquivado, concluir
  a verificação como nenhuma movimentação necessária.

## Capabilities

### Novas capabilities

- `openspec/change-archive-management`: restauração segura de mudanças
  concluídas do diretório de arquivo para o diretório ativo do OpenSpec.

### Capabilities modificadas

Nenhuma.

## Impacto

- **Escopo do MVP:** Não se aplica ao produto em execução; esta é uma tarefa de
  organização e manutenção dos artefatos de desenvolvimento.
- **Entidades do domínio:** nenhuma entidade de
  `docs/domain-model.md` é afetada.
- **Reuso:** utiliza a estrutura de diretórios e os artefatos OpenSpec existentes;
  não introduz código, dependências ou novas ferramentas.
- **Compatibilidade:** mantém o conteúdo e os nomes dos pacotes restaurados.
  Conflitos são reportados para resolução explícita em vez de sobrescrever
  mudanças ativas.
- **Rollback:** se necessário, os diretórios restaurados podem ser movidos de
  volta ao arquivo após verificar que a restauração não alterou seu conteúdo.
