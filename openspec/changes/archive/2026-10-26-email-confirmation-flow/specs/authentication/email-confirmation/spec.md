# Spec Delta

## Purpose

Define cadastro e login com confirmação de e-mail para Motoristas e Prestadores, incluindo prevenção de envios duplicados, reenvio controlado e tratamento de limites do provedor.

## ADDED Requirements

### Requirement: Cadastro exige confirmação de e-mail
O sistema MUST exigir que o usuário confirme o endereço de e-mail antes de permitir login após o cadastro.

#### Scenario: Cadastro envia confirmação
- **WHEN** um usuário envia dados válidos para criar uma conta
- **THEN** o sistema solicita o cadastro uma única vez, não cria sessão autenticada e informa: "Enviamos um e-mail de confirmação para <email>. Confirme para entrar. Olhe também a caixa de spam."

#### Scenario: Cadastro aceito sem sessão
- **WHEN** o Supabase aceita o cadastro mas não retorna sessão por exigir confirmação
- **THEN** o sistema exibe a mesma orientação de confirmação e não trata a ausência de sessão como falha

### Requirement: Cadastro impede envios duplicados
O sistema MUST impedir novos envios de cadastro enquanto a requisição anterior estiver em andamento e MUST NOT repetir automaticamente uma requisição rejeitada ou expirada.

#### Scenario: Clique repetido durante cadastro
- **WHEN** o usuário aciona novamente o cadastro enquanto uma requisição está em andamento
- **THEN** o sistema não envia outra solicitação e mantém o botão desabilitado até a primeira resposta

#### Scenario: Cadastro falha
- **WHEN** uma requisição de cadastro falha por HTTP 429 ou outro erro
- **THEN** o sistema não executa retry automático e permite nova tentativa manual quando apropriado

### Requirement: Limite de cadastro mostra orientação segura
Quando o Supabase limita o cadastro, o sistema MUST exibir uma mensagem em português sem expor conteúdo bruto da resposta.

#### Scenario: Cadastro recebe HTTP 429
- **WHEN** o Supabase rejeita o cadastro por excesso de tentativas
- **THEN** o sistema mostra "Muitas tentativas. Aguarde alguns minutos e tente novamente."

### Requirement: Login informa e-mail não confirmado
O sistema MUST distinguir e informar em português quando o login é recusado porque o endereço ainda não foi confirmado.

#### Scenario: Login de conta não confirmada
- **WHEN** o Supabase indica que o e-mail da conta ainda não foi confirmado
- **THEN** o sistema informa que o usuário deve confirmar o e-mail antes de entrar e oferece a ação de reenvio da confirmação

### Requirement: Reenvio de confirmação respeita intervalo mínimo
O sistema MUST permitir reenvio manual de confirmação apenas após um intervalo mínimo visível de 60 segundos entre solicitações.

#### Scenario: Primeiro reenvio
- **WHEN** o usuário solicita o reenvio e não há intervalo ativo
- **THEN** o sistema solicita um único reenvio e inicia uma contagem regressiva visível de 60 segundos

#### Scenario: Reenvio durante intervalo
- **WHEN** o usuário tenta reenviar durante a contagem regressiva
- **THEN** o botão fica desabilitado, mostra o tempo restante e nenhuma solicitação é enviada

#### Scenario: Reenvio recebe HTTP 429
- **WHEN** o Supabase limita uma solicitação de reenvio
- **THEN** o sistema mostra "Muitas tentativas. Aguarde alguns minutos e tente novamente." e não repete a solicitação automaticamente

### Requirement: Link de confirmação usa destino configurável
O sistema MUST fornecer ao Supabase um destino de redirecionamento de confirmação configurado por ambiente, sem fixar domínio no código.

#### Scenario: Destino de confirmação configurado
- **WHEN** o sistema solicita cadastro ou reenvio e existe destino configurado válido
- **THEN** a URL configurada é enviada como destino de retorno do link de confirmação

#### Scenario: Destino de confirmação ausente ou inválido
- **WHEN** o sistema solicita cadastro ou reenvio sem destino válido configurado
- **THEN** o sistema não inventa nem usa endereço fixo e apresenta um erro de configuração seguro
