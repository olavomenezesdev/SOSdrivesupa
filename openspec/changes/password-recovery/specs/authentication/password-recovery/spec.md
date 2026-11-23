# Spec Delta

## Purpose

Permite que Motoristas e Prestadores solicitem com segurança a recuperação da própria senha e definam uma nova senha a partir de um link válido do Supabase Auth.

## ADDED Requirements

### Requirement: Solicitar link de recuperação
O sistema MUST solicitar ao Supabase um link de recuperação para o e-mail informado e MUST apresentar o mesmo sucesso genérico independentemente da existência da conta.

#### Scenario: E-mail cadastrado
- **WHEN** o usuário informa um e-mail válido e a solicitação é aceita
- **THEN** o sistema mostra "Se esse e-mail estiver cadastrado, você receberá um link"

#### Scenario: E-mail não cadastrado
- **WHEN** o usuário informa um e-mail não cadastrado e o Supabase responde sem revelar a existência da conta
- **THEN** o sistema mostra a mesma mensagem genérica de sucesso

#### Scenario: Solicitação em andamento
- **WHEN** o usuário envia o formulário antes de receber a resposta
- **THEN** o botão "Enviar link de recuperação" fica desabilitado até a chamada terminar

#### Scenario: Falha na solicitação
- **WHEN** o Supabase rejeita ou não consegue concluir a solicitação
- **THEN** o sistema mostra uma mensagem amigável em português e permite tentar novamente

### Requirement: Validar acesso à redefinição
A redefinição MUST estar disponível somente depois de o Supabase emitir o evento de recuperação de senha.

#### Scenario: Página aberta por um link válido
- **WHEN** o Supabase dispara o evento `PASSWORD_RECOVERY`
- **THEN** o sistema mostra o formulário de nova senha

#### Scenario: Página aberta diretamente
- **WHEN** o usuário abre `/redefinir-senha` sem um evento válido de recuperação
- **THEN** o sistema mostra um aviso em português e oferece um link para `/esqueci-senha`

#### Scenario: Componente desmontado
- **WHEN** o usuário sai da página de redefinição
- **THEN** o listener de autenticação do componente é removido

### Requirement: Redefinir senha com validação
O sistema MUST aceitar somente uma nova senha com pelo menos 6 caracteres cuja confirmação seja igual.

#### Scenario: Senhas válidas
- **WHEN** ambas as senhas têm pelo menos 6 caracteres e são iguais
- **THEN** o sistema envia a nova senha ao Supabase para atualização

#### Scenario: Senha curta
- **WHEN** uma das senhas possui menos de 6 caracteres
- **THEN** o sistema impede a atualização e informa o requisito mínimo

#### Scenario: Confirmação diferente
- **WHEN** a confirmação não é igual à nova senha
- **THEN** o sistema impede a atualização e informa que as senhas precisam ser iguais

### Requirement: Confirmar redefinição concluída
Após a atualização bem-sucedida da senha, o sistema MUST confirmar o resultado e encaminhar o usuário ao login.

#### Scenario: Atualização aceita
- **WHEN** o Supabase aceita a nova senha
- **THEN** o sistema mostra uma mensagem de sucesso e redireciona para `/login`

#### Scenario: Atualização rejeitada
- **WHEN** o Supabase rejeita a atualização
- **THEN** o sistema mostra uma mensagem amigável em português e mantém o formulário disponível

### Requirement: Vincular recuperação ao login
A tela de login MUST oferecer acesso à jornada de recuperação de senha.

#### Scenario: Usuário esquecido da senha
- **WHEN** o usuário acessa a tela de login
- **THEN** o sistema mostra o link "Esqueci minha senha" apontando para `/esqueci-senha`
