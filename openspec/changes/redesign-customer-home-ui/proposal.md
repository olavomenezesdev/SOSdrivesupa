## Why

A tela Área do cliente precisa de uma hierarquia visual mais clara para que motoristas localizem o mapa, escolham um tipo de socorro e acompanhem o chamado sem perder os controles existentes. O padrão de cards flutuantes aproxima a experiência da tela do prestador e melhora a leitura em diferentes tamanhos de tela.

## What Changes

- Reorganizar a tela Área do cliente em um cabeçalho de marca e dois cards principais: mapa e pedido/status.
- Aplicar fundo em degradê suave, espaçamento, superfícies brancas, bordas arredondadas, sombras e contraste consistente.
- Aproveitar melhor a altura e largura da viewport, com o mapa em destaque e o painel de solicitação preenchendo o espaço útil.
- Corrigir a disposição do indicador e do contador dinâmico de profissionais disponíveis no cabeçalho.
- Apresentar os tipos de serviço em uma grade de cartões com seus ícones e ações atuais.
- Destacar o status existente do chamado e seus metadados, além de organizar os controles existentes de mensagens e cancelamento.
- Adaptar colunas e cartões a telas estreitas, sem alterar estados, eventos, rotas, mapa ou integrações.

## Capabilities

### New Capabilities
- `customer-home-ui`: apresentação responsiva e baseada em cards para a Área do cliente, preservando as interações e os dados dinâmicos já existentes.

### Modified Capabilities
- None.

## Impact

- Área visual da função de tela cliente em `sosdrive.py` e seletores correspondentes em `styles.py`.
- Nenhum impacto em APIs, estados, consultas, integrações, migrations ou entidades do domínio. A mudança permanece dentro do MVP e reutiliza o fluxo de chamado existente.
- Como nenhum dado de Chamado ou Avaliação é modificado, não há migração nem plano de rollback de dados; a reversão consiste em restaurar os wrappers e estilos visuais anteriores.
