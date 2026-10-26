# Email Confirmation Specification

## Purpose

Define cadastro e login com confirmação de e-mail para Motoristas e Prestadores, incluindo prevenção de envios duplicados, reenvio controlado e tratamento de limites do provedor.

## Requirements

### Requirement: Cadastro exige confirmação de e-mail
O sistema MUST exigir que o usuário confirme o endereço de e-mail antes de permitir login após o cadastro.

#### Scenario: Cadastro envia confirmação
- **GIVEN** um usuário com dados válidos ainda não cadastrado
- **WHEN** o usuário envia os dados para criar uma conta
- **THEN** o sistema solicita o cadastro uma única vez, não cria sessão autenticada e informa: "Enviamos um e-mail de confirmação para <email>. Confirme para entrar. Olhe também a caixa de spam."

#### Scenario: Cadastro aceito sem sessão
- **GIVEN** o Supabase exige confirmação de e-mail
- **WHEN** aceita o cadastro sem retornar sessão
- **THEN** o sistema exibe a orientação de confirmação e não trata a ausência de sessão como falha

### Requirement: Cadastro impede envios duplicados
O sistema MUST impedir novos envios de cadastro enquanto a requisição anterior estiver em andamento e MUST NOT repetir automaticamente uma requisição rejeitada ou expirada.

#### Scenario: Clique repetido durante cadastro
- **GIVEN** uma requisição de cadastro em andamento
- **WHEN** o usuário aciona novamente o cadastro
- **THEN** o sistema não envia outra solicitação e mantém o botão desabilitado até a primeira resposta

#### Scenario: Cadastro falha
- **GIVEN** uma requisição de cadastro rejeitada ou expirada
- **WHEN** a requisição falha por HTTP 429 ou outro erro
- **THEN** o sistema não executa retry automático e permite nova tentativa manual quando apropriado

### Requirement: Limite de cadastro mostra orientação segura
Quando o Supabase limita o cadastro, o sistema MUST exibir uma mensagem em português sem expor conteúdo bruto da resposta.

#### Scenario: Cadastro recebe HTTP 429
- **GIVEN** uma tentativa de cadastro
- **WHEN** o Supabase rejeita a solicitação por excesso de tentativas
- **THEN** o sistema mostra "Muitas tentativas. Aguarde alguns minutos e tente novamente."

### Requirement: Login informa e-mail não confirmado
O sistema MUST distinguir e informar em português quando o login é recusado porque o endereço ainda não foi confirmado.

#### Scenario: Login de conta não confirmada
- **GIVEN** uma conta cujo e-mail ainda não foi confirmado
- **WHEN** o Supabase recusa o login por esse motivo
- **THEN** o sistema informa que o usuário deve confirmar o e-mail antes de entrar e oferece a ação de reenvio da confirmação

### Requirement: Reenvio de confirmação respeita intervalo mínimo
O sistema MUST permitir reenvio manual de confirmação apenas após um intervalo mínimo visível de 60 segundos entre solicitações.

#### Scenario: Primeiro reenvio
- **GIVEN** que não há intervalo ativo
- **WHEN** o usuário solicita o reenvio da confirmação
- **THEN** o sistema solicita um único reenvio e inicia uma contagem regressiva visível de 60 segundos

#### Scenario: Reenvio durante intervalo
- **GIVEN** uma contagem regressiva de reenvio ativa
- **WHEN** o usuário tenta reenviar durante o intervalo
- **THEN** o botão fica desabilitado, mostra o tempo restante e nenhuma solicitação é enviada

#### Scenario: Reenvio recebe HTTP 429
- **GIVEN** uma solicitação de reenvio
- **WHEN** o Supabase limita o reenvio por excesso de tentativas
- **THEN** o sistema mostra "Muitas tentativas. Aguarde alguns minutos e tente novamente." e não repete a solicitação automaticamente

### Requirement: Link de confirmação usa destino configurável
O sistema MUST fornecer ao Supabase um destino de redirecionamento de confirmação configurado por ambiente, sem fixar domínio no código.

#### Scenario: Destino de confirmação configurado
- **GIVEN** um destino de retorno válido configurado
- **WHEN** o sistema solicita cadastro ou reenvio
- **THEN** a URL configurada é enviada como destino de retorno do link de confirmação

#### Scenario: Destino de confirmação ausente ou inválido
- **GIVEN** que não existe um destino de confirmação válido configurado
- **WHEN** o sistema solicita cadastro ou reenvio
- **THEN** o sistema não inventa nem usa endereço fixo e apresenta um erro de configuração seguro
