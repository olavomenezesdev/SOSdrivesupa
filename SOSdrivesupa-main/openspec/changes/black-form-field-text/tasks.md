## 1. Identificar os pontos de estilo

- [x] 1.1 Localizar os estilos existentes e os contêineres dos formulários de login, cadastro de cliente/motorista e cadastro de prestador, reutilizando a estrutura atual e verificando que cada seletor pode ser escopado sem afetar outras telas.

## 2. Aplicar a aparência dos campos

- [x] 2.1 Adicionar regras CSS escopadas aos três formulários para renderizar inputs, textareas e selects em `#000000`, incluindo placeholders opacos e texto de autofill, verificando que somente a cor do texto é alterada.
- [x] 2.2 Adicionar classes identificadoras aos contêineres em `sosdrive.py` somente se os estilos existentes não fornecerem seletores estáveis, verificando que componentes, eventos e propriedades funcionais permanecem inalterados. O contêiner `.login-page` existente foi suficiente; nenhum componente funcional foi alterado.

## 3. Verificar a mudança

- [x] 3.1 Executar a validação disponível do frontend e inspecionar as três telas, verificando placeholders, caracteres digitados, valores preenchidos automaticamente e conteúdo de selects em preto, além de confirmar que uma tela não solicitada e o restante do design permanecem inalterados. A sintaxe, as regras escopadas e a renderização de login/cadastro foram verificadas; os seletores novos ficam exclusivamente sob `.login-page`.
