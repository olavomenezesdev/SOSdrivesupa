# Tasks

## 1. Configuração e adapter Supabase

- [x] 1.1 Adicionar leitura e validação de `SUPABASE_EMAIL_REDIRECT_URL` sem registrar seu valor; cobrir URL ausente/inválida e válida com testes unitários.
- [x] 1.2 Reutilizar o adapter Supabase para passar `emailRedirectTo` no cadastro e implementar reenvio explícito de confirmação; verificar payloads e erros com mocks, sem chamadas reais.
- [x] 1.3 Mapear `email_not_confirmed` e HTTP 429 para erros estruturados sanitizados; verificar status/códigos e ausência de corpo bruto em testes unitários.

## 2. Cadastro com confirmação e proteção contra duplicidade

- [x] 2.1 Proteger o evento de cadastro com guarda de estado em andamento antes do I/O, não autenticar após signup e exibir o e-mail de confirmação solicitado; verificar sessão ausente/presente, limpeza da senha e nenhuma segunda chamada com testes mockados.
- [x] 2.2 Desabilitar o botão de cadastro enquanto carrega e impedir submissões concorrentes também no handler; verificar estado disabled e duplo envio bloqueado sem Supabase real.
- [x] 2.3 Mostrar exatamente a mensagem definida para HTTP 429 no cadastro, sem retry; verificar texto e contagem de uma chamada nos testes unitários.

## 3. Login e reenvio de confirmação

- [x] 3.1 Exibir orientação em português ao detectar e-mail não confirmado e oferecer a ação de reenvio; verificar mensagem e visibilidade do controle com mocks.
- [x] 3.2 Implementar cooldown de 60 segundos no estado servidor, bloqueio antes do I/O e contagem regressiva visível; verificar reenvio permitido, repetição bloqueada e liberação após expiração com relógio controlado/mocks.
- [x] 3.3 Mostrar a mensagem definida para HTTP 429 no reenvio e não repetir automaticamente; verificar uma única chamada e estado/cooldown com testes mockados.

## 4. Documentação e validação local

- [x] 4.1 Documentar `SUPABASE_EMAIL_REDIRECT_URL`, formato esperado e orientação para domínio permitido pelo Supabase em `.env.example`/README sem incluir valor real; conferir conteúdo sem abrir `.env`.
- [x] 4.2 Executar testes unitários direcionados e exportação do backend Reflex; registrar que não foram feitos cadastros reais nem alterações externas e verificar conclusão local.
  - Verificação local: 80 testes passaram (1 ignorado); exportação Reflex do backend concluiu. Não foram feitos cadastros reais nem alterações externas.

## Workflow follow-up

- Confirmar no navegador, sem gerar envios extras, que a URL configurada corresponde ao destino desejado e está permitida no painel Supabase.
- Não alterar SMTP, limites, redirect allowlist ou qualquer configuração externa do Supabase nesta change.
