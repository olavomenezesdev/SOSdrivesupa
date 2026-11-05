# Design

## Context

A landing pública atual diverge da referência visual compartilhada. O objetivo é substituir a hero atual por uma composição funcional e responsiva inspirada na referência, sem mudar as rotas e o fluxo de autenticação do app.

## Goals / Non-Goals

**Goals:**
- Reproduzir a navegação superior, o headline, a proposta de valor e a identidade visual do PNG para a rota `/`.
- Preservar a usabilidade da página em desktop e celular.
- Manter os CTAs e links navegando para as rotas existentes (`/login`, `/` etc.).
- Reaproveitar os estilos existentes em `styles.py` e a arquitetura Python + Reflex.

**Non-Goals:**
- Não criar novo framework frontend.
- Não alterar autorização, backend ou regras de autenticação.
- Não transformar a landing em imagem estática isolada; ela deve continuar sendo um layout funcional, responsivo e acessível.

## Decisions

1. **Reutilizar o recurso visual da referência local**
   - Colocar a imagem fornecida como base visual do hero, com overlay escuro para preservar legibilidade.
   - Usar a referência como guia para escala, espaçamento e tipografia, sem perder o comportamento funcional do Reflex.

2. **Substituir a hero atual por uma composição responsiva**
   - Definir um container único para a landing, com nav no topo e headline centralizado sobre a imagem de fundo.
   - Ajustar paddings, tamanhos e quebras para que a composição se comporte bem em telas estreitas.

3. **Preservar rotas de produto já existentes**
   - Os links da landing continuarão apontando para as rotas existentes do app; o objetivo da mudança é a aparência, não a jornada.

4. **Minimizar custo de manutenção**
   - Reusar tokens já definidos em `styles.py` e somente acrescentar classes novas para a landing, sem duplicar regras de design em lugares indevidos.

## Risks / Trade-offs

- A imagem de referência não é um asset do app; pode exigir ajustes finos de contraste e saturação para manter boa legibilidade.
- A composição em mobile pode sofrer contração do texto; a solução deve priorizar legibilidade без quebra de layout.
- A navegação do app deve continuar funcionando sem depender do carregamento de qualquer serviço externo.

## Migration Plan

Nenhuma migração de dados. Implementar a nova landing na rota `/`, validar que a página carrega e que links/CTAs continuam acessíveis, sem mexer em regras de autenticação ou backend.

## Open Questions

Nenhuma.
