## Why

Os textos dos campos de login e cadastro podem ficar com baixo contraste em
relação ao fundo atual, dificultando a leitura de placeholders, valores
preenchidos e caracteres digitados. Este ajuste visual torna esses textos
consistentemente pretos sem alterar o fluxo ou o restante do design.

## What Changes

- Aplicar `#000000` aos textos exibidos em inputs, textareas e selects das
  telas de login, cadastro de cliente/motorista e cadastro de prestador.
- Aplicar `#000000` aos placeholders, valores carregados automaticamente e
  texto de preenchimento automático nesses formulários.
- Restringir os seletores aos contêineres das três telas, preservando as
  demais telas e todos os estilos visuais não relacionados à cor do texto.
- Não alterar eventos, validações, handlers, rotas, autenticação ou regras de
  negócio.

## Capabilities

### New Capabilities

- `form-field-appearance`: Define a legibilidade e o escopo visual dos textos
  exibidos nos campos dos formulários de autenticação e cadastro.

### Modified Capabilities

Nenhuma.

## Impact

- Frontend Reflex/CSS, principalmente os estilos compartilhados e a
  identificação dos contêineres dos três formulários.
- Nenhum endpoint, modelo, banco de dados, entidade de domínio ou dependência
  externa será alterado.
- A mudança permanece dentro do escopo de consistência visual e UX do MVP,
  reutilizando a estrutura existente dos formulários.
