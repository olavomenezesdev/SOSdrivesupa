# Design

## Context

O projeto usa Python/Reflex e já possui integração com Supabase em `supabase_backend.py`, além de telas de login/cadastro no mesmo módulo principal. A jornada deve reutilizar esse estado visual e o cliente configurado sem introduzir dependências alternativas.

## Goals / Non-Goals

**Goals:**

- Disponibilizar recuperação e redefinição de senha nas rotas solicitadas.
- Usar o fluxo de autenticação do Supabase já configurado.
- Preservar os padrões de componentes e feedback das telas atuais.
- Impedir uso indevido da página de redefinição sem o evento válido de recuperação.

**Non-Goals:**

- Alterar cadastro, login, perfis, chamados, veículos, mensagens ou localização.
- Migrar dados ou criar novo cliente Supabase.
- Alterar configuração administrativa ou políticas Auth fora da aplicação.

## Decisions

1. **Iniciar a recuperação no cliente Supabase do navegador**
   - A chamada `resetPasswordForEmail` será iniciada no navegador para que o cliente PKCE persista o `code_verifier` no mesmo armazenamento usado ao retornar para `/redefinir-senha`.
   - O cliente usa a URL e a chave pública já configuradas para o Supabase; a atualização da senha continua no backend pelo adapter existente.
   - Alternativa considerada: iniciar a recuperação no backend. Não escolhida porque o backend não compartilha o armazenamento do navegador e o retorno `?code=...` não pode ser trocado sem o verifier PKCE.

2. **Coordenar o evento `PASSWORD_RECOVERY` na interface**
   - A página de redefinição observará o evento de autenticação do Supabase e só renderizará o formulário após `PASSWORD_RECOVERY`.
   - Alternativa considerada: confiar somente na URL. Não escolhida porque o evento é necessário para distinguir um link válido de uma abertura direta.

3. **Validar antes da atualização**
   - O frontend informará imediatamente senha curta ou confirmação diferente; o backend também validará tamanho e igualdade antes de chamar `updateUser`.
   - Alternativa considerada: validar somente no Supabase. Não escolhida porque mensagens de validação devem ser consistentes e acionáveis.

4. **Mensagens genéricas na solicitação**
   - Toda resposta do envio de recuperação exibirá, em caso de sucesso, a mesma mensagem genérica, independentemente de cadastro.
   - Alternativa considerada: informar e-mail inexistente. Não escolhida por vazamento de conta.

## Risks / Trade-offs

- [O Reflex pode não manter diretamente o listener JavaScript do Supabase] → encapsular o listener em um componente/script integrado ao fluxo Reflex e testar remoção no desmontamento.
- [O link de recuperação pode ser processado no navegador antes da montagem da página] → aguardar explicitamente o evento Auth e manter o aviso até sua ocorrência.
- [A configuração do Supabase pode rejeitar o redirect configurado] → validar a URL atual e o redirect como parte dos testes locais, sem fixar domínio no código.
- [A atualização pode ocorrer sem sessão válida] → só renderizar o formulário após `PASSWORD_RECOVERY` e tratar a rejeição como falha amigável.

## Migration Plan

1. Implementar os métodos, páginas e estado sem alterar banco ou entidades.
2. Executar testes unitários focados e um teste manual das três jornadas.
3. No rollback, remover as páginas/link do app e desativar os novos métodos; não há alteração de dados para reverter.

## Open Questions

Nenhuma.
