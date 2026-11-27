## 1. Backend: modo e confirmação simulada

- [x] 1.1 [Backend] Adicionar a configuração `APP_ENV` e habilitar o modo mock somente com `PAYMENT_MODE=mock` e `APP_ENV=development` ou `APP_ENV=test`; tratar valores ausentes/desconhecidos como não mock e verificar combinações incluindo bloqueio em produção.
- [x] 1.2 [Backend] Adicionar aprovação simulada às validações e ao processamento de confirmação existentes, sem chamada ao Asaas nem mudança de esquema; verificar autorização, atualização do estado de pagamento e ausência de chamadas externas em testes.

## 2. Integração com o fluxo existente

- [x] 2.1 Conectar a ação de pagamento já existente à confirmação mock retornada pelo backend, preservando a tela, resumo, rotas e etapas pós-pagamento; verificar avanço imediato após aprovação no ambiente de teste.
- [x] 2.2 Verificar que sem o modo mock habilitado a criação do checkout, confirmação e processamento de webhook do Asaas permanecem inalterados, usando os testes relacionados ao pagamento.

## 3. Verificação funcional

- [x] 3.1 Executar os testes automatizados focados de pagamento para confirmar isolamento em desenvolvimento/teste, bloqueio em produção, ausência de checkout no modo mock e continuidade do fluxo posterior; registrar o resultado.
