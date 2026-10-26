# Tasks

## 1. Erros de cadastro seguros

- [x] 1.1 Reutilizar o adapter Supabase existente para classificar rejeições conhecidas sem incluir corpo sensível em logs; verificar com testes unitários para HTTP 400, e-mail duplicado e erro desconhecido.
- [x] 1.2 Atualizar o estado/tela de cadastro para mostrar erro acionável sem sair da página; verificar com testes que mensagens não contêm senha, token ou chave.

## 2. Cadastro e encaminhamento ao login

- [x] 2.1 Reutilizar a tela de login e ajustar o cadastro bem-sucedido para limpar estado de autenticação e redirecionar para login; verificar os casos com sessão e sem sessão em testes Reflex.
- [x] 2.2 Atualizar README com a configuração Auth dos ambientes de teste/produção, o risco de e-mail não verificado e a ausência de migração histórica; conferir os passos documentados.

## 3. Configuração e integração

- [ ] 3.1 Configurar confirmação por e-mail desabilitada nos projetos Supabase de teste e produção conforme decisão explícita do usuário; confirmar a opção em cada painel Auth e nunca usar service-role no app.
- [x] 3.2 Reproduzir `disable_plugins`, identificar sua origem e corrigir apenas configuração Reflex do projeto se inválida; verificar exportação/inicialização sem o erro.
- [x] 3.3 Inspecionar o runtime para chamadas Xano em cadastro/login e outras jornadas; comprovar com teste ou inspeção que essas operações usam Supabase e não chamam Xano. Se outra jornada depender de Xano, abrir uma change OpenSpec separada antes de removê-la.
- [ ] 3.4 Executar verificação integrada criando contas descartáveis de cliente e prestador, confirmando redirecionamento ao login, login subsequente e feedback em cadastro rejeitado; registrar a limpeza das contas de teste.
- [x] 3.5 Executar a suíte relacionada e exportação de produção Reflex; registrar resultados locais sem afirmar que houve deploy.

## Workflow follow-up

- Definir provedor e domínio de hospedagem antes de planejar/publicar o deploy; até então o app pode ser validado apenas em localhost.
- Dados históricos do Xano (contas, chamados, mensagens, veículos e fotos) ficam fora desta mudança e não serão importados.
