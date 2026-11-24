# Tasks

## 1. Backend de recuperação

- [x] 1.1 Iniciar a solicitação de recuperação pelo cliente Supabase no navegador para persistir o verifier PKCE; manter redirect `/redefinir-senha` e resposta genérica.
- [x] 1.2 [Backend] Adicionar validação de nova senha e atualização segura pelo Supabase Auth; verificar com testes unitários para senha curta, senhas diferentes e sucesso.

## 2. Interface de recuperação

- [x] 2.1 Criar a página `/esqueci-senha` seguindo os componentes e estilos de login; iniciar recuperação no navegador e refletir carregamento, sucesso genérico e falhas.
- [x] 2.2 Criar a página `/redefinir-senha` com listener `PASSWORD_RECOVERY`, estado de verificação, aviso para abertura direta, formulário, validações e unsubscribe.
- [x] 2.3 Adicionar o link "Esqueci minha senha" à tela de login apontando para `/esqueci-senha`; verificar por inspeção visual da rota `/login`.

## 3. Verificação funcional

- [x] 3.1 Criar ou atualizar testes automatizados cobrindo chamadas Supabase, validações e estados das novas páginas; executar o menor conjunto relacionado e registrar o resultado.
- [ ] 3.2 Validar o fluxo completo em ambiente local: solicitação, retorno do link, redefinição, redirecionamento ao login e login com a nova senha.
