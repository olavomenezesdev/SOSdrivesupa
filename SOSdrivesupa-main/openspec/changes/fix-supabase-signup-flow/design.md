# Design

## Context

Veja `proposal.md` para a motivação e `specs/authentication/account-signup/spec.md` para o contrato de comportamento. O cadastro atual chama Supabase Auth pelo backend; sem sessão, mostra uma mensagem pedindo confirmação por e-mail; com sessão, mantém autenticação e redireciona para a home. As falhas HTTP não expõem o motivo ao usuário.

## Goals / Non-Goals

**Goals:**

- Reutilizar o fluxo atual de cadastro e o login Supabase.
- Após sucesso, limpar tokens de sessão do estado Reflex e redirecionar para a rota de login.
- Dar feedback de erro seguro e distinguível para e-mail já cadastrado, dados/configuração rejeitados e falhas de conectividade.
- Fazer o funcionamento sem confirmação depender da configuração Auth dos projetos Supabase de teste e produção, e não de uma confirmação simulada no cliente.
- Confirmar que cadastro e login não chamam Xano; encaminhar qualquer outra dependência ativa encontrada para uma change própria.
- Diagnosticar a mensagem `disable_plugins` separadamente, confirmando sua origem na inicialização Reflex antes de alterar configuração.
- Validar localmente. Publicação não faz parte desta execução porque não há provedor/domínio de produção definido.

**Non-Goals:**

- Migrar usuários ou dados históricos do Xano.
- Adicionar envio de e-mail, serviço de confirmação ou dependência externa.
- Usar credencial service-role no app ou marcar usuários como confirmados por código cliente.
- Publicar em hospedagem ainda não definida.

## Decisions

1. **Desabilitar confirmação nos projetos Supabase de teste e produção**
   - Por decisão explícita do usuário, configurar a opção de confirmação por e-mail como desativada nos projetos Auth que atendem esses ambientes.
   - A aplicação não contorna a política: não usa service-role nem simula confirmação no frontend.
   - Alternativa considerada: confirmação por e-mail em produção; não escolhida porque o usuário informou que não dispõe desse fluxo de e-mail.

2. **Redirecionar para login após sucesso**
   - A navegação de sucesso é sempre para login; limpar tokens/access state no fluxo de cadastro. Um retorno sem sessão é erro de configuração e não pode ser apresentado como cadastro utilizável.
   - Reutilizar a tela/rota existente de login.
   - Alternativa considerada: autenticar imediatamente e abrir a home. Isso contradiz a jornada solicitada.

3. **Erro categorizado no backend, mensagem segura na interface**
   - Preservar o status HTTP e traduzir apenas causas conhecidas para mensagens acionáveis; para causa desconhecida, exibir texto genérico com o status e manter detalhes sensíveis fora da interface e dos logs.
   - Não ecoar o corpo bruto de erro do Supabase, pois pode conter dados de entrada.
   - Alternativa considerada: expor a exceção integral ao usuário; rejeitada por privacidade e segurança.

4. **Separar o aviso `disable_plugins` do erro de signup**
   - Reproduzir a inicialização e identificar se a mensagem é emitida pelo Reflex ou por sua configuração/dependência antes de editar esse ponto. Corrigir somente se houver configuração inválida ligada ao app.
   - Tratar o HTTP 400 do Supabase como falha independente, mesmo que a mensagem de plugins apareça no mesmo terminal.

## Risks / Trade-offs

- [Desabilitar confirmação em produção reduz a verificação de propriedade do e-mail e facilita contas com endereços de terceiros] → decisão informada pelo usuário; não coletar nem registrar segredos, monitorar abuso e reavaliar a ativação de envio de e-mail antes de ampliar a operação.
- [O HTTP 400 pode decorrer de entradas, senha, provedor ou configuração do Supabase] → mapear somente causas comprovadas e manter fallback seguro que mostre o status para diagnóstico.
- [Contas previamente criadas sem confirmação podem continuar sem acesso] → verificar a conta de teste e orientar o reenvio do cadastro/login conforme o estado retornado, sem alterar usuários automaticamente.
- [A configuração externa do Supabase não pode ser validada sem acesso administrativo ao projeto] → deixar a tarefa pendente até confirmação no painel; nunca ler ou imprimir credenciais do `.env`.
- [Sem provedor/domínio, produção não pode ser publicada] → limitar conclusão a build/testes locais e declarar deploy pendente, sem afirmar que o app está online.

## Migration Plan

1. Implementar e testar mensagens, limpeza de sessão e navegação sem alterar schema ou dados.
2. No painel Auth dos projetos Supabase de teste e produção, desabilitar confirmação de e-mail; validar a alteração administrativamente antes de considerar signup pronto.
3. Testar criação de conta de cliente e prestador e login subsequente; verificar que erros continuam na página de cadastro.
4. Confirmar por teste/inspeção que cadastro e login não dependem do Xano. Se outra jornada runtime ainda depender dele, planejar sua remoção em change OpenSpec separada.
5. Não migrar contas ou dados históricos do Xano. A preparação local não equivale a deploy; o deploy depende da escolha de hospedagem.
6. Rollback: reverter apenas a alteração de fluxo no app e restaurar a configuração de confirmação anterior nos projetos; não há migração de banco.

## Open Questions

Nenhuma. A mudança de configuração Auth é restrita ao ambiente de teste solicitado.
