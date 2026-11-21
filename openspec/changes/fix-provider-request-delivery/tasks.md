## 1. Diagnóstico e inicialização

- [x] 1.1 Reproduzir a entrada na Área do Prestador com a sessão autenticada e instrumentar montagem, identidade disponível, contagens retornadas e atualização do State sem registrar dados pessoais; verificar os logs e identificar a etapa que falha.
- [x] 1.2 Na rota `/home_provider`, reutilizar o carregamento pontual na entrada e iniciar um único polling de fundo sem competir com a carga inicial; preservar o polling independente da rota `/provider` e verificar primeira carga, guarda contra duplicação e atualização recorrente com testes.
- [x] 1.3 Garantir que erro de autenticação/evento/backend seja apresentado como erro com retry, não como lista vazia; verificar respostas vazias e falhas com testes focados.

## 2. Integridade da fila

- [x] 2.1 Reutilizando a RPC autorizada existente, manter Chamados pendentes retornados visíveis mesmo quando suas coordenadas estão ausentes ou inválidas, sem descartar os demais; verificar o resultado e a distância indisponível com testes.
- [x] 2.2 Preservar a combinação e deduplicação de pendentes e ativos, inclusive o badge “Em andamento” e a possibilidade de aceitar um pendente; verificar com testes de regressão.
- [x] 2.3 Confirmar que apenas Prestadores autenticados recebem a fila pelo backend e que logs não incluem token, dados de contato, identificadores pessoais ou coordenadas; verificar testes de autorização/logs sem mudanças de schema/RLS.

## 3. Verificação integrada

- [x] 3.1 Executar os testes focados da fila e a compilação Reflex; confirmar que ambos passam.
- [x] 3.2 Validar manualmente em sessões distintas que um chamado criado pelo Cliente aparece para o Prestador, pode ser aceito e continua visível como ativo; se a sessão real receber zero/erro da RPC apesar de haver chamados elegíveis, comparar a função implantada e informar o SQL/RLS necessário antes de propor qualquer alteração.
