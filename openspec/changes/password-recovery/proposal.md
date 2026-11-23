# Proposal

## Why

Usuários que esquecem a senha atualmente não possuem uma jornada segura para solicitarem o restabelecimento ou definirem uma nova senha. O SOS Drive já usa Supabase Auth, então a recuperação deve reutilizar essa integração sem depender de outra tecnologia ou expor se um e-mail está cadastrado.

## What Changes

- Adicionar a página `/esqueci-senha` com solicitação de link de recuperação pelo Supabase Auth.
- Adicionar a página `/redefinir-senha`, disponível somente após o evento `PASSWORD_RECOVERY`.
- Validar senha mínima de 6 caracteres e confirmação igual antes de atualizar a senha.
- Adicionar o link "Esqueci minha senha" na tela de login.
- Manter os padrões visuais, de navegação e estado das telas existentes em Python/Reflex.

## Capabilities

### New Capabilities

- `authentication/password-recovery`: solicitação segura de recuperação e atualização de senha com Supabase Auth.

### Modified Capabilities

Nenhuma.

## Impact

- Dentro do escopo do MVP: autenticação e recuperação de acesso de Motoristas e Prestadores.
- Não cria nem altera Motorista, Prestador, Chamado, Tipo de Socorro, Avaliação ou Localização.
- Reutiliza o cliente Supabase já configurado no backend e os componentes visuais da tela de login.
- Não altera chamadas Xano, dados persistidos nem funcionalidades não relacionadas.
- Não há migração de dados nem rollback de banco necessário.
