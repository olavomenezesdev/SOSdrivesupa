# Design

## Context

Consulte `proposal.md` e `specs/authentication/email-confirmation/spec.md`. O app usa Supabase Auth pelo backend Python e Reflex para o cadastro/login. O envio de confirmação e o SMTP já são responsabilidade da configuração Supabase existente; esta change não altera recursos externos.

## Goals / Non-Goals

**Goals:**

- Reutilizar a tela e o estado Reflex de autenticação, impedindo execução concorrente de signup e de reenvio.
- Usar o retorno sem sessão do Supabase como fluxo normal de cadastro pendente de confirmação.
- Manter a senha fora do estado após resposta, preservar e-mail para o aviso/login e nunca autenticar automaticamente o usuário não confirmado.
- Validar `SUPABASE_EMAIL_REDIRECT_URL` no backend e passá-la como `emailRedirectTo` nas chamadas de cadastro/reenvio, sem gravar ou registrar o valor.
- Aplicar cooldown de 60 segundos no reenvio com horário de término no estado Reflex servidor, contagem visível e bloqueio da operação enquanto o cooldown estiver ativo.
- Mapear HTTP 429 para a mensagem solicitada e não fazer retry automático.
- Testar integração de estado e adapter com mocks; nenhuma chamada real de signup ou resend.

**Non-Goals:**

- Alterar SMTP, limites ou qualquer outra configuração externa do Supabase.
- Migrar dados históricos, adicionar provedores de e-mail ou contornar rate limits.
- Exigir que o cooldown sobreviva a logout, reinício do backend ou uma nova sessão/dispositivo; o limite de segurança definitivo continua sendo do Supabase Auth.

## Decisions

1. **Tratar signup sem sessão como confirmação pendente**
   - Após retorno normal sem sessão, informar o e-mail de destino e permanecer em estado não autenticado; a tela pode oferecer navegação para login e reenvio.
   - Alternativa considerada: interpretar ausência de sessão como erro; isso quebra o comportamento padrão quando confirmação está habilitada.

2. **Impedir duplicidade antes de I/O**
   - Conferir `is_loading` antes de iniciar signup/resend e ativá-lo antes de ceder controle; a interface também desabilita o botão durante a requisição.
   - Nenhum callback de página inicia cadastro; nenhum retry automático é adicionado. Erros 429 não geram novo envio.
   - Alternativa considerada: confiar apenas no botão desabilitado; não impede eventos repetidos enviados diretamente ao backend.

3. **Reenvio com cooldown e rate limit do provedor**
   - Guardar timestamp de término do cooldown no estado Reflex servidor. O evento de reenvio verifica o tempo antes de chamar Auth; um timer/refresh da tela atualiza o contador visível.
   - Após uma chamada aceita ou limitada (429), manter bloqueio mínimo de 60 segundos; exibir a mesma mensagem de limite em caso de 429.
   - O cooldown é proteção de UX por sessão e não substitui o rate limit Supabase, que permanece soberano entre sessões.
   - Alternativa considerada: memória global por e-mail, rejeitada por não ser consistente em múltiplos workers e por reter identificadores.

4. **Configuração de retorno sem domínio embutido**
   - Ler `SUPABASE_EMAIL_REDIRECT_URL` das configurações backend, validar esquema HTTP(S) e host, e falhar com mensagem segura se ausente/inválida.
   - Passar a URL via opções Auth `emailRedirectTo`; não interpolar credenciais e não registrá-la.
   - Alternativa considerada: URL local/de produção hard-coded, rejeitada por impedir ambientes diferentes e arriscar destino incorreto.

5. **Erros de confirmação e 429**
   - Converter `email_not_confirmed` em erro Auth estruturado, apresentar orientação em português e oferecer reenvio. Para 429 no cadastro/reenvio, mostrar exatamente: “Muitas tentativas. Aguarde alguns minutos e tente novamente.”
   - Não expor corpo ou exceção bruta; não repetir a chamada.

## Risks / Trade-offs

- [SMTP pode rejeitar envio ou Supabase pode manter limite ativo] → mostrar 429 com orientação, aplicar cooldown e não retry; o usuário pode tentar manualmente mais tarde.
- [Cooldown local não impede tentativas em outra sessão/dispositivo] → manter Supabase como rate limiter autoritativo e explicitar que não há bypass.
- [URL de redirect ausente ou fora da allowlist Supabase] → validar presença/formato no app e documentar que o domínio também deve estar autorizado no painel, sem editar essa configuração.
- [Contagem regressiva em navegador suspenso pode atrasar atualização] → calcular segundos restantes a partir do timestamp e recalcular em cada tick/evento, sem depender de contagem decremental acumulada.

## Migration Plan

1. Configurar `SUPABASE_EMAIL_REDIRECT_URL` no ambiente local e demais ambientes a partir de um domínio já permitido no Supabase; não alterar configurações externas nesta mudança.
2. Implementar e testar adapter, estado, mensagens e cooldown com mocks.
3. Executar testes unitários e exportação Reflex sem cadastros reais; testar manualmente apenas navegação/timer sem enviar formulário.
4. Rollback: reverter o fluxo de resend/signup e remover a variável de ambiente; sem alteração de banco ou de configuração SMTP.

## Open Questions

Nenhuma. A variável escolhida é `SUPABASE_EMAIL_REDIRECT_URL`; o valor é fornecido pelo usuário no ambiente e nunca deve ser exibido em logs.
