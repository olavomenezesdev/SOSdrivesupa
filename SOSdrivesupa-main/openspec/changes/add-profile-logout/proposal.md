## Why

Usuários autenticados precisam encerrar a sessão de forma visível e previsível ao sair do perfil, especialmente em dispositivos compartilhados. A aplicação já possui limpeza local da sessão e redirecionamento para login, mas a tela de perfil não oferece uma ação de saída.

## What Changes

- Adicionar à página de perfil uma ação “Sair”, destacada no cabeçalho e visualmente distinta do botão “Voltar”.
- Ao acionar “Sair”, limpar as credenciais e os dados de usuário mantidos no estado Reflex e redirecionar para `/login`.
- Reutilizar o fluxo existente de logout e limpeza de sessão, sem criar um endpoint ou alterar o schema do banco.

## Capabilities

### New Capabilities

- `authentication/logout`: define o encerramento explícito de sessão a partir da página de perfil, incluindo limpeza do estado autenticado e retorno ao login.

### Modified Capabilities

Nenhuma. A confirmação de e-mail não é afetada.

## Impact

- **MVP:** dentro do escopo de autenticação e navegação essencial.
- **Código:** estado `AuthState` e componente `profile_screen` em `sosdrive.py`; os métodos existentes `logout` e `clear_session` devem ser reutilizados.
- **Sistemas e dados:** a mudança limpa tokens e dados de usuário do estado Reflex; não altera tabelas, migrations, integrações de chamados ou o modelo de domínio Motorista/Prestador.
- **APIs e dependências:** sem novos endpoints ou pacotes; o fluxo permanece em Python/Reflex.
- **Verificação:** cobrir limpeza dos campos autenticados, redirecionamento ao login e presença do botão na tela de perfil.
