# 🚗 SOS Drive

Experiência web **mobile-first** desenvolvida em **Python + Reflex** para conectar motoristas que enfrentam emergências veiculares a prestadores de assistência próximos, centralizando geolocalização, comunicação em tempo real, pagamento integrado e acompanhamento completo do chamado.

<p align="center">
  <!-- IMAGEM 01: Banner ou captura da página inicial pública (Landing Page) -->
  <img src="./assets/docs/01-landing-page.png" alt="Tela inicial pública do SOS Drive" width="800" />
</p>

---

## 📑 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Perfis e Controle de Acesso](#-perfis-e-controle-de-acesso)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura e Estrutura](#-arquitetura-e-estrutura)
- [Configuração e Execução Local](#-configuração-e-execução-local)
- [Manual de Utilização](#-manual-de-utilização)
- [Exemplos Práticos de Uso](#-exemplos-práticos-de-uso)
- [Limitações Conhecidas](#-limitações-conhecidas)

---

## 📌 Sobre o Projeto

O **SOS Drive** resolve a dificuldade de encontrar assistência veicular rápida e confiável em situações como **pneu furado, bateria descarregada, pane mecânica ou falta de combustível**.

A aplicação separa a apresentação pública — voltada para apresentar o serviço e gerar confiança — das rotas internas operacionais:
- **Para Motoristas (Clientes):** solicitação estruturada de socorro, seleção do veículo, estimativa de distância e valor, pagamento integrado, chat e acompanhamento do atendimento.
- **Para Prestadores de Serviço:** controle de disponibilidade, fila de chamados próximos, visualização de dados do veículo/cliente, rotas em mapa e gestão das etapas até a conclusão.

### Tecnologias e Serviços Integrados
- **Frontend & Backend:** Python + [Reflex](https://reflex.dev/)
- **Autenticação, Banco de Dados e Storage:** [Supabase](https://supabase.com/) (Auth, PostgreSQL com RLS e Storage)
- **Mapas e Rotas:** Leaflet, OpenStreetMap, OSRM e integração externa com Google Maps
- **Pagamentos (Sandbox):** Gateway [Asaas](https://www.asaas.com/) (Checkout e Webhooks)

---

## 👥 Perfis e Controle de Acesso

O acesso às áreas operacionais exige autenticação por e-mail e senha, com controle de permissões garantido pelo backend e pelas políticas de segurança (RLS) do Supabase. Atualmente, o sistema contempla dois perfis (não há perfil administrativo implementado):

| Perfil | Responsabilidades | Permissões Principais | Restrições |
| :--- | :--- | :--- | :--- |
| **Cliente / Motorista** | Manter dados pessoais atualizados, cadastrar veículos, informar localização, pagar pelo serviço e avaliar o atendimento. | Gerenciar próprio perfil e veículos; criar chamados; cancelar chamados pendentes; enviar mensagens e avaliar o prestador. | Precisa ter ao menos 1 veículo cadastrado para abrir chamado; não pode aceitar/concluir chamados nem cancelar após aceitação. |
| **Prestador de Serviço** | Informar disponibilidade, analisar chamados próximos, deslocar-se até o cliente, atualizar etapas e concluir o atendimento. | Consultar fila de chamados; aceitar, liberar ou concluir atendimentos sob sua responsabilidade; enviar aviso de chegada, mensagens e avaliar o cliente. | Não pode criar chamados em nome de clientes nem acessar chamados aos quais não esteja autorizado. |

---

## ✨ Funcionalidades

- **Página Pública e UX Responsiva:** apresentação inicial com componentes Reflex, estilos centralizados em `styles.py` e suporte a `prefers-reduced-motion`.
- **Cadastro, Login e Recuperação de Senha:** criação de conta com seleção de perfil, confirmação de e-mail (com reenvio protegido por intervalo de 60s), restauração de sessão e redefinição de senha via e-mail.
- **Perfil e Gestão de Veículos:** atualização de nome, CPF, telefone e foto de perfil (PNG/JPEG); cadastro, listagem e remoção de veículos (marca, modelo, placa, ano e cor).
- **Solicitação de Assistência:** escolha entre 4 categorias (*pneu furado, bateria, mecânica e combustível*), seleção de veículo, geolocalização via navegador e cálculo de distância/preço estimados.
- **Pagamentos Integrados:** checkout integrado ao Asaas para validação e confirmação da solicitação antes da liberação aos prestadores.
- **Painel Operacional do Prestador:** controle de disponibilidade, fila de chamados por proximidade, validação concorrente no backend (evita que dois prestadores aceitem o mesmo chamado), liberação e conclusão.
- **Mapas e Geolocalização:** marcadores interativos, cálculo de distância, traçado de rotas (Leaflet, OpenStreetMap, OSRM) e atalho para navegação externa no Google Maps.
- **Comunicação em Andamento:** painel de mensagens com atualização automática a cada 2 segundos e botão de **Avisar Chegada** com notificação automática ao cliente.
- **Avaliação Mútua:** após o encerramento do chamado, tanto o cliente quanto o prestador podem avaliar a experiência.

---

## 🏗️ Arquitetura e Estrutura

```text
SOSdrive/
├── sosdrive.py                  # Lógica principal da aplicação Reflex
├── sosdrive_app/                # Entry point do projeto Reflex
├── styles.py                    # Tokens de cor e CSS global compartilhado
├── assets/                      # Ilustrações locais opcionais (PNG/WebP) e imagens da doc
├── scripts/                     # Scripts utilitários (ex: aplicação de migrations)
├── supabase/migrations/         # Migrations SQL versionadas do projeto
├── requirements.txt             # Dependências Python
├── setup.ps1                    # Script auxiliar de instalação no Windows
├── .env.example                 # Modelo de variáveis de ambiente (sem credenciais)
└── openspec/                    # Propostas e especificações do projeto
```

> Ilustrações em `assets/` são opcionais e a ausência delas não impede a inicialização da aplicação.

---

## ⚙️ Configuração e Execução Local

Atualmente o SOS Drive não possui ambiente público em produção. Para utilizá-lo, execute-o localmente seguindo as etapas abaixo.

### 1. Pré-requisitos
- **Python 3.12+** instalado
- Projeto **Supabase** configurado (com provedor Email habilitado no Supabase Auth)
- Navegador moderno com JavaScript habilitado, conexão com a internet e permissão de localização

### 2. Variáveis de Ambiente (`.env`)
Crie um arquivo `.env` na raiz do projeto (ao lado de `sosdrive.py`) baseado no [`.env.example`](./.env.example). O `.env` é ignorado pelo Git e variáveis exportadas no ambiente têm precedência.

#### Configuração essencial (Supabase)
```dotenv
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<publishable-or-anon-key>
SUPABASE_EMAIL_REDIRECT_URL=http://localhost:3000/login
```

- `SUPABASE_ANON_KEY`: utilize a chave pública (`publishable`/`anon`). **Nunca** exponha a `service-role key` no navegador, Git ou logs.
- `SUPABASE_EMAIL_REDIRECT_URL`: endereço HTTP(S) de destino após a confirmação de e-mail (precisa estar autorizado nas *Redirect URLs* do Supabase Auth).

#### Configuração opcional de Pagamentos (Asaas Sandbox)
Para habilitar o checkout e webhooks em ambiente de testes, adicione também:

```dotenv
ASAAS_API_KEY=<sua-chave-sandbox-asaas>
ASAAS_WEBHOOK_TOKEN=<token-secreto-do-webhook>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key-somente-backend>
ASAAS_CHECKOUT_RETURN_URL=https://<seu-tunel-ngrok-porta-8000>
ASAAS_CHECKOUT_FRONTEND_URL=http://localhost:3000
```

- `SUPABASE_SERVICE_ROLE_KEY` é usada **exclusivamente no backend**.
- `ASAAS_CHECKOUT_RETURN_URL` deve apontar para a origem HTTPS pública encaminhada à porta `8000` do backend (ex.: túnel ngrok), que redirecionará o retorno para `ASAAS_CHECKOUT_FRONTEND_URL`.
- No painel Asaas Sandbox:
  1. Configure o webhook para `<ASAAS_CHECKOUT_RETURN_URL>/api/asaas/webhook` usando o mesmo `ASAAS_WEBHOOK_TOKEN`.
  2. Habilite os eventos `CHECKOUT_PAID`, `CHECKOUT_CANCELED` e `CHECKOUT_EXPIRED`.
  3. Cadastre uma chave Pix na conta Sandbox caso queira testar pagamentos via Pix.

> ⚠️ **Reinicie o backend** sempre que alterar o arquivo `.env`.

### 3. Banco de Dados e Migrations (Supabase)
As migrations versionadas em `supabase/migrations/` já estão prontas para uso. Para executar a aplicação normalmente, **não é necessário** informar a URI PostgreSQL (`SUPABASE_DB_URL`).

> **Nota sobre dados legados:** O histórico anterior do Xano (contas, veículos, chamados, mensagens e fotos) permanece preservado no workspace original, mas **não é importado** para o app. Cada usuário deve criar uma nova conta no Supabase.

Somente para **manutenção de schema**, copie a URI PostgreSQL em **Supabase → Connect** (prefira *Session pooler* em redes IPv4 exigindo SSL) e defina `SUPABASE_DB_URL` localmente:

```bash
# Consultar migrations pendentes sem alterar o banco
.venv/bin/python -m scripts.apply_supabase_migrations

# Aplicar migrations após confirmar que a URI aponta para o projeto correto
.venv/bin/python -m scripts.apply_supabase_migrations --apply
```

*(A aplicação é transacional e a migration inicial se recusa a sobrescrever tabelas do SOS Drive já existentes.)*

### 4. Instalação e Execução

> ⚠️ Execute o Reflex **sempre** pelo ambiente virtual (`.venv`) do projeto. Rodar `reflex run` globalmente pode apontar para outro Python sem o cliente Supabase e gerar `ImportError: cannot import name 'Client' from 'supabase'`.

#### Windows (PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\reflex.exe run
```

*(Opcional: para definir variáveis diretamente na sessão PowerShell antes de rodar)*
```powershell
$env:SUPABASE_URL = "https://<project-ref>.supabase.co"
$env:SUPABASE_ANON_KEY = "<publishable-or-anon-key>"
```

#### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/reflex run
```

Após iniciar, acesse **`http://localhost:3000`** no navegador.

> **Sobre e-mail de confirmação:** com a confirmação ativa no Supabase Auth, a conta não é autenticada automaticamente após o cadastro. O reenvio respeita intervalo de 60 segundos; em caso de `HTTP 429` (limite de taxa), aguarde alguns minutos antes de tentar novamente.

<details>
<summary><strong>🔧 Opções Avançadas: Demonstração em Rede Wi-Fi e Conflito de Portas</strong></summary>

#### Apresentação em dois computadores na mesma rede Wi-Fi (macOS)
Descubra o IPv4 do Mac anfitrião e exponha o backend na rede local:

```bash
export SOSDRIVE_DEMO_HOST="$(ipconfig getifaddr en0)"
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m reflex run --backend-host 0.0.0.0
```

- Mantenha o terminal aberto e permita conexões de entrada (Python/Node) no firewall do macOS.
- Nos dois computadores (mesmo Wi-Fi), acesse `http://<IP-DO-MAC>:3000` (não use `localhost` no segundo computador).
- Utilize duas contas Supabase distintas (um cliente com veículo cadastrado e um prestador).

#### Escolher portas livres no Windows (PowerShell)
Se as portas padrão (`3000` / `8000`) estiverem ocupadas, inicie em portas alternativas e valide a conectividade:

```powershell
.venv\Scripts\reflex.exe run --frontend-port 3001 --backend-port 8100

# Validar escuta e saúde dos serviços
Test-NetConnection -ComputerName localhost -Port 3001
Test-NetConnection -ComputerName localhost -Port 8100
Get-NetTCPConnection -LocalPort 3001,8100 -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort, OwningProcess
Invoke-WebRequest -Uri http://localhost:3001 -UseBasicParsing
Invoke-WebRequest -Uri http://localhost:8100/_health -UseBasicParsing
```

Confirme `TcpTestSucceeded : True` e respostas HTTP válidas antes de abrir `http://localhost:3001`.

</details>

---

## 📖 Manual de Utilização

### 1. Primeiro Acesso, Cadastro e Login
1. Acesse a página inicial e selecione **Criar conta**.
2. Escolha o perfil (**Cliente/Motorista** ou **Prestador de Serviço**), preencha nome, e-mail e senha e confirme.
3. Se a confirmação de e-mail estiver ativa, valide o link enviado à sua caixa de entrada.
4. Na tela **Entrar**, informe suas credenciais (ou use **Esqueci minha senha** para redefinição por e-mail). O sistema redireciona automaticamente para a Home correspondente ao seu perfil.

<p align="center">
  <!-- IMAGEM 02: Telas de Cadastro e Login -->
  <img src="./assets/docs/02-autenticacao-cadastro-login.png" alt="Telas de cadastro, login e recuperação de senha" width="750" />
</p>

---

### 2. Jornada do Cliente / Motorista

#### Perfil e Cadastro de Veículos
- Acesse **Perfil** para atualizar nome, CPF, telefone e foto de perfil.
- Em **Meus Veículos**, clique em **Adicionar veículo** e informe marca, modelo, placa, ano e cor. Também é possível consultar ou **Remover** veículos cadastrados.

<p align="center">
  <!-- IMAGEM 03: Home do Cliente, Perfil e Cadastro de Veículos -->
  <img src="./assets/docs/03-cliente-home-veiculos.png" alt="Home do cliente e gerenciamento de veículos" width="750" />
</p>

#### Solicitação de Assistência e Pagamento
1. Na Home, clique em **Pedir socorro** e conceda permissão de localização ao navegador.
2. Selecione o tipo de ocorrência (*Pneu furado, Bateria, Mecânica ou Combustível*) e escolha o veículo cadastrado.
3. Confira as estimativas de distância e preço e avance para o pagamento.
4. No checkout integrado, escolha a forma de pagamento disponível e conclua a transação. Após a confirmação, o chamado é validado e exibido aos prestadores autorizados.

<p align="center">
  <!-- IMAGEM 04: Painel de solicitação de socorro e estimativa -->
  <img src="./assets/docs/04-cliente-solicitar-socorro.png" alt="Tela de solicitação de assistência veicular" width="360" />
  &nbsp;&nbsp;
  <!-- IMAGEM 05: Confirmação do pagamento realizado -->
  <img src="./assets/docs/05-cliente-confirmacao-pagamento.png" alt="Confirmação do pagamento realizado" width="360" />
</p>

#### Acompanhamento, Chat, Cancelamento e Avaliação
- **Acompanhamento:** observe a evolução do status em tempo real até que um prestador aceite o chamado.
- **Cancelamento:** disponível via **Cancelar Pedido** *somente enquanto o chamado estiver pendente e sem prestador associado*.
- **Comunicação:** use o painel de mensagens do chamado para conversar com o prestador (atualizado automaticamente enquanto aberto).
- **Avaliação:** ao término do atendimento, registre sua nota e avaliação sobre o profissional.

<p align="center">
  <!-- IMAGEM 06: Acompanhamento do chamado e chat com o prestador -->
  <img src="./assets/docs/06-cliente-acompanhamento-chat.png" alt="Acompanhamento do chamado e chat" width="360" />
  &nbsp;&nbsp;
  <!-- IMAGEM 07: Avaliação do Prestador de Serviço -->
  <img src="./assets/docs/07-cliente-avaliacao-prestador.png" alt="Formulário de avaliação do prestador" width="360" />
</p>

---

### 3. Jornada do Prestador de Serviço

#### Home, Disponibilidade e Fila de Chamados
1. Na Home operacional do prestador, ative o controle **Disponível** para passar a visualizar solicitações próximas.
2. Analise os chamados pendentes (tipo de serviço, dados básicos do veículo e distância aproximada) e clique em **Aceitar chamado**.
3. O backend garante atomicidade na aceitação, impedindo que dois prestadores assumam a mesma solicitação.

<p align="center">
  <!-- IMAGEM 08: Home do Prestador com mapa, disponibilidade e fila de chamados -->
  <img src="./assets/docs/08-prestador-home-chamados.png" alt="Home do prestador com disponibilidade e solicitações próximas" width="750" />
</p>

#### Deslocamento, Atendimento, Liberação e Conclusão
- **Deslocamento e Rota:** visualize o marcador do cliente no mapa e clique em **Abrir GPS** para navegação externa.
- **Comunicação:** utilize o chat integrado e clique em **Avisar Chegada** ao alcançar o local (envia notificação automática ao cliente).
- **Liberar Chamado:** caso não consiga prosseguir nas etapas permitidas, use a opção de cancelamento/liberação e confirme no modal (**Sim, cancelar**) para devolver o chamado à fila pendente.
- **Concluir Atendimento:** finalize o serviço clicando em **Concluir atendimento** para exibir o resumo final.

<p align="center">
  <!-- IMAGEM 09: Atendimento em andamento, rota e aviso de chegada -->
  <img src="./assets/docs/09-prestador-atendimento-rota.png" alt="Tela de atendimento em andamento com mapa e mensagens" width="750" />
</p>

#### Avaliação do Cliente / Motorista
Após concluir o atendimento, o prestador acessa a opção de avaliação na tela de encerramento para classificar a experiência com o cliente.

<p align="center">
  <!-- IMAGEM 10: Opção de avaliação do cliente após a conclusão do atendimento -->
  <img src="./assets/docs/10-prestador-opcao-avaliacao.png" alt="Opção de avaliação do cliente após conclusão do atendimento" width="360" />
  &nbsp;&nbsp;
  <!-- IMAGEM 11: Formulário de avaliação do Cliente/Motorista -->
  <img src="./assets/docs/11-prestador-formulario-avaliacao.png" alt="Formulário de avaliação do Cliente/Motorista" width="360" />
</p>

---

## 🧪 Exemplos Práticos de Uso

<details>
<summary><strong>Clique para expandir os cenários demonstrativos (dados fictícios)</strong></summary>

1. **Cadastro e Primeiro Acesso (Ana Santos):** cria conta como *Cliente/Motorista*, valida o e-mail, faz login e cadastra seu *Chevrolet Onix 2022* (placa fictícia `ABC1D23`).
2. **Solicitação por Pneu Furado + Pagamento (Ana Santos):** clica em *Pedir socorro*, autoriza a localização, escolhe *Pneu Furado* e o *Onix*, confere distância e preço estimados, realiza o pagamento pelo gateway integrado e acompanha a busca por prestadores.
3. **Aceitação e Conclusão (Carlos Oliveira):** entra como *Prestador de Serviço*, ativa a disponibilidade, aceita o chamado de Ana, usa a navegação externa até o local, conversa pelo chat, aciona *Avisar Chegada*, realiza a troca e clica em *Concluir atendimento*.
4. **Avaliação Mútua (Ana e Carlos):** após o encerramento, Ana avalia o atendimento de Carlos e Carlos registra sua avaliação sobre Ana.
5. **Solicitação por Bateria Descarregada (Bruno Alves):** acessa a conta, seleciona *Pedir socorro*, compartilha a localização, escolhe a categoria *Bateria* para seu *Volkswagen Polo 2021* e acompanha o chamado pelo mesmo fluxo padrão.
6. **Recuperação de Senha (Mariana):** na tela de login, clica em *Esqueci minha senha*, informa o e-mail cadastrado, acessa o link recebido para definir uma nova senha e volta a fazer login normalmente.

</details>

---

## ⚠️ Limitações Conhecidas

- **Hospedagem:** ainda não há versão pública publicada em produção; o uso depende de execução local ou ambiente disponibilizado pelo responsável.
- **Histórico de Atendimentos:** ainda não existe uma tela dedicada para listagem completa de chamados anteriores (o atalho *Histórico* na Home do cliente redireciona para o Perfil).
- **Edição de Veículos:** embora o backend suporte atualização de veículos, a interface atual expõe apenas cadastro, visualização e remoção.
- **Persistência de Dados do Prestador:** especialidades e status de disponibilidade são exibidos na interface, mas sua persistência entre sessões ou dispositivos distintos ainda não foi confirmada.
- **Interface de Atendimento e Rota Legada:** alguns controles na tela de detalhes estão incompletos (o acompanhamento operacional deve ser feito pela tela de *atendimento em andamento*); existe ainda uma rota legada de prestador com dados simulados que não reflete o fluxo integrado ao Supabase.
- **Dependências Externas e Permissões:** o funcionamento completo exige conexão com internet, credenciais válidas do Supabase/Asaas e permissão de geolocalização no navegador. Recursos de mapas/rotas dependem da disponibilidade de Leaflet, OpenStreetMap, OSRM e Google Maps. O upload de fotos via Supabase Storage aceita arquivos **PNG** ou **JPEG** dentro do limite de tamanho configurado.
