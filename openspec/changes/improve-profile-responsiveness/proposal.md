## Why

A página de perfil deve permanecer legível e utilizável em celulares, tablets e desktops. A estrutura atual já possui regras responsivas, mas ainda precisa de uma revisão integrada para evitar conteúdo apertado, cortes e rolagem horizontal em larguras menores.

## What Changes

- Definir comportamento adaptativo para o cabeçalho, resumo do perfil, formulário, lista de veículos e barra de salvamento.
- Ajustar espaçamentos, largura dos cards e disposição dos campos para diferentes larguras de tela.
- Preservar textos, ações, eventos, estados e integrações existentes.
- Validar a página em larguras representativas de celular, tablet e desktop, incluindo ausência de overflow horizontal.

## Capabilities

### New Capabilities

- `profile/responsive-layout`: especifica o comportamento responsivo da página de perfil.

### Modified Capabilities

Nenhuma.

## Impact

- **MVP:** dentro do escopo; melhora a usabilidade da edição do perfil existente.
- **Código:** estilos da página de perfil em `styles.py` e, somente se necessário para a disposição visual, a composição Reflex em `sosdrive.py`.
- **Sistemas e dados:** sem mudanças em backend, estados, persistência, APIs ou entidades do domínio.
- **Tecnologias:** reutiliza Reflex e CSS já adotados.
- **Verificação:** testes existentes, compilação Reflex e inspeção visual em larguras móveis, tablet e desktop.
