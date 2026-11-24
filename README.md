# SOS Drive

Experiência web mobile-first em Python + Reflex para conectar motoristas a assistência veicular.

## Começar pelo lugar certo

A primeira tela é uma apresentação pública, pensada para explicar o serviço e gerar confiança. A operação acontece separadamente na Home interna.

```text
SOSdrive/
├── sosdrive.py                  # Lógica da aplicação Reflex
├── sosdrive_app/                # Entry point do projeto Reflex
├── styles.py                     # Tokens e CSS compartilhados
├── assets/                       # Ilustrações locais opcionais (PNG/WebP)
├── requirements.txt             # Dependências Python
├── setup.ps1                    # Instalação no Windows
└── openspec/                   # Propostas e especificações
```

## Executar

Crie um arquivo `.env` na raiz do projeto (ao lado de `sosdrive.py`) e
configure as credenciais públicas do projeto Supabase:

```dotenv
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<publishable-or-anon-key>
SUPABASE_EMAIL_REDIRECT_URL=https://your-domain.example/login
```

O arquivo `.env` é local e ignorado pelo Git. O backend carrega esse arquivo ao
iniciar; variáveis já exportadas no ambiente têm precedência. Um modelo sem
valores reais está em [`.env.example`](./.env.example).
`SUPABASE_EMAIL_REDIRECT_URL` deve ser um destino HTTP(S) para o qual o usuário
será enviado após confirmar o e-mail. O endereço também precisa estar permitido
nas URLs de redirecionamento do Supabase Auth para o projeto correspondente.

## Supabase e dados

O app usa Supabase Auth, PostgreSQL e Storage para cadastro/login, perfis,
veículos, chamados e mensagens. As migrations versionadas em
`supabase/migrations/` já foram aplicadas ao projeto configurado. Para executar
o app, não é necessária a URI PostgreSQL nem a service-role key.

Use a publishable/anon key como `SUPABASE_ANON_KEY`. A service-role key ignora
RLS e não é necessária para o runtime; nunca a coloque no browser, Git ou logs.
O banco começa sem importação de contas, registros ou fotos históricas do Xano.
Cada usuário precisa criar uma nova conta Supabase. O workspace Xano e seus
dados permanecem preservados, mas não são usados pelo app.

Somente para manutenção de schema, copie a URI PostgreSQL em **Supabase →
Connect** e guarde-a localmente como `SUPABASE_DB_URL`. Prefira Session pooler
em redes IPv4 e exija SSL. Nunca compartilhe a URI ou senha.

Para consultar as migrations sem conectar ao banco:

```bash
.venv/bin/python -m scripts.apply_supabase_migrations
```

Só aplique depois de conferir que a URI aponta para o projeto correto:

```bash
.venv/bin/python -m scripts.apply_supabase_migrations --apply
```

O aplicador registra cada versão de forma transacional. A migration inicial
recusa criar tabelas do SOS Drive se já encontrar tabelas-alvo preexistentes.

No macOS/Linux, instale e inicie assim:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/reflex run
```

Sempre execute o Reflex pelo ambiente virtual do projeto. O comando `reflex
run` fora do `.venv` pode usar outra instalação do Python que não contém o
cliente Supabase e falhar com `ImportError: cannot import name 'Client' from
'supabase'`. Se o ambiente virtual ainda não existir, crie-o antes da
instalação:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m reflex run
```

No Windows/PowerShell, também é possível definir as variáveis diretamente na
sessão:

```powershell
$env:SUPABASE_URL = "https://<project-ref>.supabase.co"
$env:SUPABASE_ANON_KEY = "<publishable-or-anon-key>"
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\reflex.exe run
```

Reinicie o backend depois de alterar o `.env`. Abra `http://localhost:3000` no
navegador. Para usar cadastro com confirmação, mantenha o provedor Email e a
confirmação de e-mail habilitados no Supabase Auth. O app informa que enviou a
confirmação, não autentica automaticamente a conta e oferece reenvio com
intervalo de 60 segundos. Se o Supabase responder `HTTP 429`, o app pede para
aguardar alguns minutos e não repete a solicitação automaticamente. O histórico
do Xano (contas, chamados, mensagens, veículos e fotos) não é importado;
usuários precisam criar novas contas Supabase.

Para pagamentos sandbox, configure `ASAAS_API_KEY`, `ASAAS_WEBHOOK_TOKEN`,
`SUPABASE_SERVICE_ROLE_KEY`, `ASAAS_CHECKOUT_RETURN_URL` e
`ASAAS_CHECKOUT_FRONTEND_URL` no `.env`.
`SUPABASE_SERVICE_ROLE_KEY` é usada somente pelo backend e nunca deve ser
exposta ao navegador. `ASAAS_CHECKOUT_RETURN_URL` deve ser a origem HTTPS
pública que encaminha ao backend (por exemplo, o domínio do túnel ngrok para a
porta 8000); os retornos do Checkout passam por rotas do backend e redirecionam
para `ASAAS_CHECKOUT_FRONTEND_URL` (em desenvolvimento,
`http://localhost:3000`). No painel Asaas, configure o webhook em
`<ASAAS_CHECKOUT_RETURN_URL>/api/asaas/webhook`, use o mesmo token e habilite
`CHECKOUT_PAID`, `CHECKOUT_CANCELED` e `CHECKOUT_EXPIRED`.
Para usar Pix no Sandbox, cadastre uma chave Pix na conta Asaas Sandbox.
Depois de configurar `SUPABASE_DB_URL`, aplique as migrations pendentes com:

```bash
.venv/bin/python scripts/apply_supabase_migrations.py --apply
```

Para apresentar em dois computadores na mesma rede Wi-Fi, descubra o IPv4 do
Mac que executará o app e inicie o Reflex usando esse endereço:

```bash
export SOSDRIVE_DEMO_HOST="$(ipconfig getifaddr en0)"
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m reflex run --backend-host 0.0.0.0
```

O terminal precisa continuar aberto. No computador do Mac, e também no do
professor/colega, abra `http://<IP-DO-MAC>:3000` (não use `localhost` no
segundo computador). Os dois computadores devem estar na mesma rede; permita conexões de entrada do
Python/Node no firewall do macOS. Crie contas Supabase diferentes para cliente
e prestador; o cliente deve cadastrar um veículo. O chamado, a aceitação e as
mensagens serão persistidos no Supabase. O painel consulta mensagens a cada
dois segundos enquanto estiver aberto.

Se as portas padrão estiverem ocupadas, escolha portas livres explicitamente:

```powershell
.venv\Scripts\reflex.exe run --frontend-port 3001 --backend-port 8100
Test-NetConnection -ComputerName localhost -Port 3001
Test-NetConnection -ComputerName localhost -Port 8100
Get-NetTCPConnection -LocalPort 3001,8100 -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort, OwningProcess
Invoke-WebRequest -Uri http://localhost:3001 -UseBasicParsing
Invoke-WebRequest -Uri http://localhost:8100/_health -UseBasicParsing
```

Confirme `TcpTestSucceeded : True` para ambas e respostas HTTP bem-sucedidas
antes de abrir `http://localhost:3001`. A consulta ao listener identifica o
processo que já ocupa cada porta; se houver conflito, escolha outras portas
livres em vez de encerrar um processo que possa pertencer a outro projeto.

## Regra de arquitetura

O frontend é escrito em Python usando Reflex. As jornadas operacionais de
cliente e prestador estão disponíveis nas rotas autenticadas documentadas
neste README.

## UX e animações

A apresentação usa componentes e estado do Reflex:

- componentes Reflex para uma composição responsiva e legível
- CSS global Reflex para o movimento visual da apresentação
- estado Reflex para navegação e feedback do login
- `prefers-reduced-motion` para respeitar usuários que preferem menos animação

O módulo `styles.py` concentra os tokens de cor e os estilos globais Reflex.
Ilustrações em `assets/` são opcionais e a ausência delas não impede a aplicação de iniciar.