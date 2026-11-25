## 1. Auditoria e inventário

- [x] 1.1 Registrar estado inicial do Git e inventariar arquivos repetidos por nome/hash, candidatos a backup e scripts avulsos; verificar cada candidato com busca global de referências antes de decidir.
- [x] 1.2 Mapear todos os rastros Xano (pasta, script, testes, imports, símbolos, variáveis e fallbacks) e confirmar usos em testes, rotas, configuração Reflex, scripts e CI antes de classificar cada item.
- [x] 1.3 Inspecionar referências e uso de `migration_safety.py`, assets duplicados, `sosdrive_atual_backup.py`, `test_urls.py` e testes Xano; registrar decisão manter/remover/duvidoso com evidência no relatório final.

## 2. Limpeza segura

- [x] 2.1 Remover somente arquivos Xano exclusivos sem referências ativas confirmadas e retirar referências/código morto estritamente relacionados; verificar que testes e módulos ativos não importam símbolos removidos.
- [x] 2.2 Remover duplicatas, backups, scripts ou assets apenas quando conteúdo e uso confirmarem uma cópia não referenciada; preservar essenciais e itens ambíguos/históricos.
- [x] 2.3 Verificar que nenhum arquivo protegido foi editado ou removido (`supabase/`, `supabase_config.py`, `supabase_backend.py`, `requirements.txt` e arquivos essenciais); revisar `git diff --name-status` e `git diff -- supabase/`.

## 3. Validação e relatório

- [x] 3.1 Executar `python -m unittest discover -s tests` e corrigir somente falhas causadas por referências a código removido do Xano; registrar falhas ambientais sem mascará-las.
- [x] 3.2 Compilar e importar `sosdrive.py`, `sosdrive_app/sosdrive_app.py` e `supabase_backend.py`, e validar inicialização Reflex com o ambiente do projeto; registrar comandos e resultados.
- [x] 3.3 Revisar os fluxos de autenticação, recuperação de senha, áreas cliente/prestador e perfil/logout por testes existentes e inspeção de diffs; apresentar relatório com removidos, modificados, mantidos/duvidosos e validações.
