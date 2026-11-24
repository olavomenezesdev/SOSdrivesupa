# Tasks

## 1. Backend e autorização

- [x] 1.1 [Backend] Criar configuração Asaas sandbox por variáveis de ambiente sem credenciais no repositório; verificar testes de configuração e ausência da chave em logs.
- [x] 1.2 [Backend] Persistir e consultar pagamentos vinculados ao Chamado concluído e ao motorista proprietário; verificar migração e testes de autorização.
- [x] 1.3 [Backend] Permitir somente criação de cobrança de cartão de crédito no Asaas usando o valor persistido do Chamado; rejeitar Pix e pagamento presencial no backend e verificar testes unitários e sandbox.
- [x] 1.4 [Backend] Implementar webhook idempotente para confirmar ou registrar falha da cobrança; verificar assinatura, duplicidade e transições válidas.
- [x] 1.5 [Backend] Reconciliar pagamentos pendentes consultando pagamentos Asaas pelo identificador do Checkout; confirmar somente cobrança única com valor correspondente e status `CONFIRMED` ou `RECEIVED`; testar resultados pendentes, ambíguos e divergentes.
- [x] 1.6 [Backend] Persistir um lançamento de ganho por Chamado confirmado, usando o valor total do serviço, sem duplicação por webhook/reconciliação; consultar saldo somente do Prestador autenticado.

## 2. Interface de pagamento

- [x] 2.1 Reutilizar o status `completed` para abrir uma nova tela `/payment` ou rota equivalente após conclusão; verificar redirecionamento e bloqueio de Chamados inválidos.
- [x] 2.2 Criar a tela no estilo do anexo com resumo do atendimento à esquerda e formas de pagamento à direita; verificar visual desktop/mobile.
- [x] 2.3 Remover Pix e pagamento presencial da interface e manter somente Checkout hospedado de cartão de crédito no Asaas; verificar estados sem pagamento confirmado.
- [x] 2.4 Exibir o total persistido e abrir Checkout Asaas seguro para coleta dos dados de cartão; verificar retorno e atualização do status.
- [x] 2.5 Criar tela de aguardando pagamento do Prestador após conclusão e bloquear retorno à Home até confirmação; verificar pendente e confirmado.
- [x] 2.6 Atualizar o estado manualmente consultando o backend, que reconcilia pendências com o Asaas antes de retornar o estado persistido; verificar confirmação e permanência pendente.
- [x] 2.7 Exibir na conta do Prestador o total dos ganhos confirmados, sem indicar transferência ou saque automático.

## 3. Avaliações pós-pagamento

- [x] 3.1 Criar persistência de avaliações por Chamado, avaliador e avaliado com unicidade; verificar autorização e duplicidade.
- [x] 3.2 Criar telas de avaliação para Motorista e Prestador após pagamento confirmado; verificar nota, comentário e único envio por participante.
- [x] 3.3 Exibir nota média e avaliações recebidas no perfil de cada participante; verificar privacidade e cálculo da média.
- [x] 3.4 Garantir que o Prestador envie a avaliação usando o identificador do Chamado aceito quando `request_id` estiver vazio; testar envio e erro sem Chamado identificável.
- [x] 3.5 Retornar o Motorista para `/home_client` após enviar a avaliação ou reconhecer que ela já foi registrada.

## 4. Verificação funcional

- [x] 4.1 Atualizar testes automatizados para garantir que somente Checkout de cartão esteja disponível e cobrir a reconciliação do Asaas, mantendo cobertura de webhook, aguardando pagamento e avaliações; executar o menor conjunto relacionado.
- [ ] 4.2 Validar o fluxo sandbox ponta a ponta com um Chamado concluído: resumo, Checkout de cartão, confirmação, bloqueio do prestador e avaliações.
- [x] 4.3 Testar que ganhos só são creditados após confirmação, sem duplicação, que apenas o Prestador dono consulta o saldo e que o Motorista retorna à Home inclusive quando já existe avaliação.
