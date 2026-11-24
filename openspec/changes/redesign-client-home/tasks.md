# Tasks

## 1. Mapear a Home atual e preparar a composição visual

- [x] 1.1 Identificar em `sosdrive.py` todos os estados, handlers, condições,
  rotas e componentes usados pela Home do Cliente e registrar sua
  correspondência na nova composição; verificar por inspeção que nenhuma
  funcionalidade existente ficou sem ponto de entrada.
- [x] 1.2 Reorganizar a composição Reflex da Home do Cliente reutilizando os
  estados e eventos existentes para mapa, localização, disponibilidade,
  seleção de serviço, veículo, chamado ativo e mensagens; verificar com
  exportação Reflex que a tela compila sem criar dependências novas.

## 2. Aplicar o redesign responsivo

- [x] 2.1 Implementar a hierarquia visual da referência com mapa em destaque,
  controles sobrepostos, indicador de profissionais, endereço atual, cartões
  de serviço e ações principais; verificar visualmente a paridade em viewport
  desktop.
- [x] 2.2 Ajustar os estilos compartilhados e específicos da Home para
  responsividade, estados selecionado/desabilitado/carregando e acessibilidade
  sem alterar tokens ou telas não relacionadas; verificar visualmente em
  viewport móvel e desktop.
- [x] 2.3 Preservar os estados de localização indisponível, loading, erro,
  chamado pendente/ativo e mensagens dentro do novo layout; verificar cada
  estado por teste existente ou reprodução manual documentada no resultado.

## 3. Verificar paridade funcional

- [x] 3.1 Executar os testes relacionados ao estado e à solicitação do Cliente,
  verificando seleção de serviço, validações, envio do chamado e polling sem
  alteração de payload ou rota.
- [x] 3.2 Executar a exportação Reflex e verificar manualmente que o Cliente
  consegue selecionar serviço, abrir mensagens, solicitar socorro e continuar
  acompanhando o chamado exatamente como antes.
