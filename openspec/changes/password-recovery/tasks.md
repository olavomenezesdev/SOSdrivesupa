# Tasks

## 1. Backend de recuperação

- [x] 1.1 Reutilizar o cliente Supabase existente para adicionar solicitação de link de recuperação e validação de e-mail; verificar com testes unitários que a chamada usa o redirect `/redefinir-senha` e não revela se o e-mail existe.
- [x] 1.2 [Backend] Adicionar validação de nova senha e atualização segura pelo Supabase Auth; verificar com testes unitários para senha curta, senhas diferentes e sucesso.

## 2. Interface de recuperação

- [ ] 2.1 Criar a página `/esqueci-senha` seguindo os componentes e estilos de login; verificar manualmente o envio, estado de carregamento, sucesso genérico e falha amigável.
- [ ] 2.2 Criar a página `/redefinir-senha` com listener `PASSWORD_RECOVERY`, aviso para abertura direta, formulário, validações e unsubscribe; verificar manualmente os cenários válido e direto.
- [x] 2.3 Adicionar o link "Esqueci minha senha" à tela de login apontando para `/esqueci-senha`; verificar por inspeção visual da rota `/login`.

## 3. Verificação funcional

- [x] 3.1 Criar ou atualizar testes automatizados cobrindo chamadas Supabase, validações e estados das novas páginas; executar o menor conjunto relacionado e registrar o resultado.
- [ ] 3.2 Validar o fluxo completo em ambiente local: solicitação, retorno do link, redefinição, redirecionamento ao login e login com a nova senha.
