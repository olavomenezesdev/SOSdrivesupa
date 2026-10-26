# Proposal

## Why

O cadastro atual depende da confirmação por e-mail, que não está disponível, e apresenta uma falha HTTP 400 sem orientação suficiente. Isso impede testar contas de cliente e prestador. Por decisão explícita do usuário, o cadastro em produção também permitirá login sem confirmação; essa escolha reduz a garantia de propriedade do e-mail.

## What Changes

- Permitir cadastro e login sem confirmação por e-mail nos ambientes Supabase de teste e produção, mediante configuração Auth explícita; não simular confirmação nem marcar contas como confirmadas pelo frontend.
- Após um cadastro concluído com sucesso, encaminhar o usuário à tela de login, sem iniciar uma sessão autenticada automaticamente.
- Exibir mensagens de erro seguras e úteis quando o Supabase rejeitar o cadastro, sem registrar ou revelar senha, tokens ou chaves.
- Investigar e corrigir a mensagem/configuração `disable_plugins` se ela vier da inicialização Reflex; tratá-la separadamente da rejeição HTTP 400 do Supabase.
- Confirmar se os fluxos executados em runtime ainda dependem do Xano; se houver dependência ativa além deste fluxo, abrir uma change específica antes de remover código.
- Não importar contas, chamados, mensagens, veículos ou fotos históricas do Xano, conforme decisão do usuário.
- Preparar e validar o app localmente; não declarar ou executar deploy sem provedor e domínio de hospedagem definidos.

## Capabilities

### New Capabilities

- `authentication/account-signup`: cadastro de motorista e prestador via Supabase sem confirmação por e-mail no ambiente MVP, redirecionamento ao login e feedback de falha.

### Modified Capabilities

Nenhuma.

## Impact

- Dentro do escopo do MVP: cadastro de motoristas e prestadores, conforme `docs/project-overview.md`.
- Impacta somente a criação/autenticação do Motorista e do Prestador; não altera Chamado, Tipo de Socorro, Avaliação ou Localização.
- Reutiliza o fluxo de cadastro e o adapter Supabase existentes em `sosdrive.py` e `supabase_backend.py`, com testes correspondentes.
- Exige alterar a configuração de confirmação de e-mail nos projetos Supabase de teste e produção. Essa configuração é externa ao repositório e não deve ser contornada com service-role key no cliente.
- Não inclui migração histórica nem publicação: não há destino de hospedagem informado; até o momento o app só foi executado em localhost.
- Não altera dependências ou tecnologias: permanece Python, Reflex e Supabase.
