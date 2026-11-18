# Proposal

## Why

The signup flow needs to use the project's configured SMTP confirmation instead of treating signup as a fully active account. Repeated manual submissions can consume Supabase Auth email limits, so the app must prevent duplicate requests and provide a controlled resend path.

## What Changes

- Require email confirmation for newly registered accounts; after signup, show the destination email and spam-folder guidance without authenticating the user.
- Prevent duplicate signup requests while one request is in progress, disable the submit button, and never retry automatically.
- Map HTTP 429 to the requested Portuguese wait message without exposing raw provider errors.
- Add a resend-confirmation action with visible 60-second cooldown, no automatic retries, and the same safe 429 handling.
- Configure `emailRedirectTo` from a validated environment setting rather than a hard-coded URL.
- Explain unconfirmed-email login failures clearly in Portuguese and cover these behaviors with mocked unit tests only.

## Capabilities

### New Capabilities

- `authentication/email-confirmation`: confirmation-required signup, confirmation messaging and redirect, safe resend throttling, duplicate-submit prevention, and handling of unconfirmed login.

### Modified Capabilities

Nenhuma.

## Impact

- Dentro do escopo do MVP: cadastro e autenticação de Motoristas e Prestadores.
- Impacta somente identidade/autenticação; não altera Chamado, Tipo de Socorro, Avaliação ou Localização.
- Reutiliza o fluxo atual Reflex e o adapter Supabase em Python; não introduz tecnologia ou dependência externa.
- Usa o SMTP já configurado pelo usuário no Supabase. A aplicação não altera configuração externa, não lê/exibe `.env` e não usa cadastro de teste real.
- `emailRedirectTo` será configurado por variável de ambiente documentada, validada sem imprimir seu valor.
