# Spec Delta

## Purpose

Define o cadastro de Motoristas e Prestadores no SOS Drive, incluindo o encaminhamento ao login sem confirmação por e-mail em teste e produção, bem como o tratamento seguro de falhas.

## ADDED Requirements

### Requirement: Cadastro sem confirmação por e-mail nos ambientes configurados
O sistema MUST permitir que um usuário crie e use uma conta com e-mail e senha sem confirmação por e-mail nos projetos Supabase de teste e produção configurados para o SOS Drive.

#### Scenario: Conta criada sem confirmação por e-mail
- **WHEN** um usuário informa dados válidos e o Supabase aceita o cadastro sem confirmação por e-mail
- **THEN** o sistema informa que a conta foi criada e encaminha o usuário para a tela de login

#### Scenario: Login após cadastro
- **WHEN** o usuário informa as credenciais válidas da conta recém-criada na tela de login
- **THEN** o sistema autentica o usuário sem exigir confirmação por e-mail

### Requirement: Cadastro bem-sucedido encaminha ao login
Após a criação bem-sucedida da conta, o sistema MUST encaminhar o usuário à tela de login sem manter uma sessão autenticada automaticamente.

#### Scenario: Cadastro retorna uma sessão Supabase
- **WHEN** a conta é criada e o Supabase retorna uma sessão
- **THEN** o sistema descarta o estado de sessão do cadastro, exibe confirmação de sucesso e encaminha o usuário à tela de login

### Requirement: Erros de cadastro são acionáveis e não expõem segredos
Quando o Supabase rejeitar um cadastro, o sistema MUST apresentar uma mensagem segura e útil, preservar a tela de cadastro e não expor senha, tokens ou chaves.

#### Scenario: Supabase rejeita dados ou configuração
- **WHEN** a API de cadastro responde com erro HTTP, incluindo status 400
- **THEN** o sistema apresenta uma explicação apropriada ao erro conhecido ou uma mensagem genérica com o status, sem apresentar conteúdo secreto ou dados sensíveis da resposta

#### Scenario: Rejeição de cadastro mantém o formulário
- **WHEN** o Supabase rejeita o cadastro
- **THEN** o sistema mantém o usuário na tela de cadastro para corrigir os dados ou tentar novamente

#### Scenario: Erro de cadastro nos logs
- **WHEN** uma falha de cadastro é registrada para diagnóstico
- **THEN** o registro contém somente contexto não sensível, como a operação e o status HTTP, e exclui senha, token, chave e corpo sensível da requisição

### Requirement: Runtime de autenticação usa Supabase
As operações de cadastro e login MUST usar Supabase e não depender de endpoints Xano.

#### Scenario: Cadastro e login disponíveis sem Xano
- **WHEN** o usuário cria uma conta ou autentica uma conta existente no SOS Drive
- **THEN** a operação é concluída pelo Supabase sem chamar endpoint Xano
