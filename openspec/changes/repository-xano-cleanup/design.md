## Context

Consulte [proposal.md](./proposal.md) para motivação, escopo e limites. A limpeza abrange arquivos de aplicação, testes, scripts, assets e código legado, mas não permite editar configuração ou lógica protegida do Supabase. O inventário e a busca por referências devem preceder cada exclusão.

## Goals / Non-Goals

**Goals:**

- Distinguir referências ativas de menções históricas antes de remover arquivos ou símbolos.
- Remover resíduos do Xano que sejam exclusivos e não necessários; preservar histórico OpenSpec e qualquer candidato ambíguo.
- Demonstrar por testes/imports e diff que fluxos atuais e arquivos protegidos permanecem intactos.

**Non-Goals:**

- Alterar comportamento funcional, banco de dados, configuração Auth, dependências ou arquitetura.
- Remover documentação histórica só por conter a palavra Xano.
- Fazer limpeza ampla de código sem relação demonstrável com os candidatos confirmados.

## Decisions

1. **Criar inventário antes de apagar**
   - Registrar candidatos, hashes/conteúdo para detectar duplicatas, referências por busca global e decisão (manter/remover/consultar).
   - Para cada exclusão, buscar o nome e os símbolos no repositório, cobrindo imports, rotas, configuração Reflex, testes, scripts e assets. A ausência de referências textuais não basta se houver carregamento dinâmico ou uso por convenção.
   - Alternativa considerada: remover a lista de arquivos indicada no pedido sem confirmação de uso. Rejeitada para reduzir risco de quebrar execução e ferramentas.

2. **Separar legado executável de histórico**
   - Excluir `xano/`, `xano_smoke_test.sh` e teste de integração apenas após confirmar que são exclusivos do provedor removido e não estão ligados por CI/scripts.
   - Tratar specs de migração, decisões e outros documentos históricos como não executáveis; mantê-los e reportá-los para decisão do usuário.
   - Alternativa considerada: apagar todo texto que menciona Xano. Rejeitada porque apagaria contexto de migração sem remover dependência ativa.

3. **Remover trechos mortos cirurgicamente**
   - Localizar código legado por busca e referências/uso de símbolos; retirar apenas declarações e caminhos Xano sem chamadas ativas.
   - Não alterar `supabase_backend.py`, `supabase_config.py`, `requirements.txt` nem qualquer conteúdo em `supabase/`.
   - Alternativa considerada: refatorar os módulos inteiros para padronizar o backend. Rejeitada por exceder o escopo.

4. **Validar antes de fechar**
   - Executar `python -m unittest discover -s tests`, compilação/imports dos módulos indicados e inicialização/validação Reflex disponível no projeto.
   - Comparar o diff de `supabase/` e arquivos protegidos com o estado inicial; qualquer modificação inesperada deve ser revertida apenas se criada nesta mudança, nunca por checkout global.
   - Se os testes falharem por ambiente/dependência ausente, registrar o erro e tentar o ambiente já configurado no projeto, sem alterar manifestos para contornar.

## Risks / Trade-offs

- [Busca textual pode não encontrar carregamento dinâmico ou convenções de nome] → inspecionar rotas, configuração, scripts e padrões de execução antes de excluir.
- [Testes de integração dependem de serviços externos] → executar a suíte solicitada e relatar claramente pré-condições/falhas ambientais, sem enfraquecer os testes.
- [Arquivos duplicados podem ter usos diferentes por caminho] → comparar conteúdo e referências de cada cópia; preservar a versão referenciada.
- [Resíduos Xano em documentação OpenSpec podem parecer código ativo] → manter documentos históricos e listá-los para decisão, conforme pedido.

## Migration Plan

1. Capturar estado inicial do Git e inventariar duplicatas, não utilizados e referências Xano.
2. Registrar candidatos e justificativas; parar e pedir confirmação se houver dependência ou uso ambíguo.
3. Excluir só os candidatos aprovados pela auditoria e retirar referências de código ativas sem tocar áreas protegidas.
4. Rodar validações e revisar os diffs protegidos; em rollback, restaurar somente os arquivos desta mudança a partir do Git.

## Open Questions

Nenhuma para a proposta. Candidatos ambíguos serão mantidos e apresentados ao usuário durante a auditoria, sem bloquearem a limpeza dos arquivos confirmados.
