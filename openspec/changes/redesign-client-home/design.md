# Design

## Context

Veja [proposal.md](./proposal.md) para a motivação e
[specs/client-home/spec.md](./specs/client-home/spec.md) para o contrato
visual e funcional. A Home do Cliente já possui estado Reflex para mapa,
localização, serviço selecionado, veículo, mensagens, criação de chamado e
acompanhamento; o redesign deve reutilizar essa infraestrutura.

## Goals / Non-Goals

**Goals:**

- Reestruturar a composição visual da Home em camadas: mapa superior,
  controles flutuantes e painel inferior de solicitação.
- Reutilizar os estados e handlers existentes, conectando os mesmos eventos
  aos novos componentes visuais.
- Reutilizar o mapa Leaflet, os tokens de `styles.py` e os padrões de
  responsividade já usados no projeto.
- Manter validação, autorização e chamadas de dados no backend/estado Reflex;
  nenhum controle visual será considerado uma regra de autorização.
- Ler e atualizar somente os dados já usados pela Home do Cliente: localização,
  perfil, veículo, disponibilidade de prestadores e chamado ativo. Nenhuma
  entidade nova será criada.

**Non-Goals:**

- Alterar endpoints, payloads, migrations, políticas RLS ou integrações
  Supabase.
- Alterar o fluxo do Prestador, o domínio dos chamados ou o cálculo de
  disponibilidade/distância.
- Adicionar busca de endereço, pagamentos, avaliação ou novas jornadas.

## Decisions

1. **Manter o estado atual e trocar somente a composição**
   - A nova tela será construída sobre os mesmos `OperationalState` vars e
     eventos já usados na Home do Cliente.
   - Alternativa rejeitada: criar uma segunda Home ou duplicar handlers, pois
     isso permitiria divergência de comportamento.

2. **Mapa como camada visual superior**
   - O mapa existente continuará sendo inicializado pelo script atual, com
     controles de localização e disponibilidade sobrepostos via Reflex.
   - O painel de solicitação ficará sobreposto ou abaixo do mapa conforme a
     largura, sem desmontar o mapa durante a seleção.
   - Alternativa rejeitada: substituir Leaflet por outro mapa, pois não há
     necessidade funcional e isso introduziria dependência e risco.

3. **Cartões de serviço preservam seleção e estimativas**
   - Os cartões reutilizarão os valores atuais de tipo, ícone e estimativa,
     alterando apenas hierarquia, espaçamento, bordas e estado selecionado.
   - O CTA continuará chamando o mesmo evento de submissão e respeitando
     veículo, localização e validações existentes.

4. **Mensagens e estados transitórios continuam acessíveis**
   - O botão/painel de mensagens, loading, erros e chamado ativo permanecerão
     presentes em posições compatíveis com o novo layout.
   - O backend continua responsável por autenticação, autorização e
     validação; a mudança não criará atalhos client-side.

## Risks / Trade-offs

- [O mapa pode ocupar espaço excessivo em telas pequenas] → usar alturas
  responsivas e manter o painel rolável, validando viewport móvel e desktop.
- [A reorganização pode ocultar estados de erro ou chamado ativo] → manter
  cenários de loading, erro, chamado pendente e chamado ativo na verificação.
- [A referência usa conteúdo visual que pode não existir nos dados atuais] →
  exibir somente dados já fornecidos pelo estado, com fallbacks existentes,
  sem inventar dados persistidos.

## Migration Plan

1. Identificar a composição atual da Home do Cliente e mapear cada evento,
   estado e condição que precisa ser preservado.
2. Refatorar a composição Reflex e os estilos relacionados, sem alterar
   funções de backend, payloads ou rotas.
3. Executar testes relacionados e exportação Reflex.
4. Validar visualmente seleção de serviço, solicitação, mensagens, localização,
   loading, erro e chamado ativo em desktop e viewport móvel.
5. Rollback: restaurar a composição e estilos anteriores; não há migração de
   dados nem alteração externa.
