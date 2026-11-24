# Proposal

## Why

A nova referência visual da Home do Cliente organiza o mapa, a localização
atual, a disponibilidade de prestadores e a escolha do tipo de socorro em uma
única experiência mais clara. A mudança deve modernizar a apresentação sem
alterar as funcionalidades, estados, chamadas ao Supabase, rotas ou regras de
solicitação já existentes.

## What Changes

- Redesenhar visualmente a Home do Cliente para seguir a referência fornecida:
  mapa em destaque no topo, indicador de profissionais disponíveis, marcador
  da localização atual, seletor de endereço e cartões de tipos de socorro.
- Reorganizar visualmente a ação principal de solicitar socorro e a ação de
  mensagens do chamado, mantendo seus eventos e condições atuais.
- Preservar seleção de serviço, localização, veículo, submissão de chamado,
  polling de status, mensagens, estados de carregamento/erro e navegação.
- Manter o layout responsivo para desktop e telas menores, adaptando a
  composição da referência sem introduzir dependências ou APIs novas.
- Não modificar regras de negócio, payloads, endpoints, persistência,
  autorização ou comportamento do prestador.

## Capabilities

### New Capabilities

- `client-home`: apresentação visual da Home do Cliente, incluindo mapa,
  localização, disponibilidade de prestadores e ações de solicitação.

### Modified Capabilities

Nenhuma.

## Impact

- Afeta principalmente a composição Reflex da Home do Cliente em
  `sosdrive.py` e seus estilos em `styles.py`.
- Pode exigir ajustes em CSS e scripts de mapa já existentes, sem alterar a
  integração de dados ou as funções de estado.
- Não altera dependências, schema Supabase, endpoints, rotas ou contratos de
  autenticação.
- A verificação deve confirmar paridade funcional com a Home atual e
  correspondência visual com a referência fornecida.
