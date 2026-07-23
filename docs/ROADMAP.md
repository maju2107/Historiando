# Roadmap do vertical slice

Este roadmap traduz o documento **Mecânicas por Ato/Missão - Historiando** para
entregas pequenas no repositório atual. O primeiro marco é a introdução na
Megafauna; sistemas dos Atos 1 a 3 entram depois que esse fluxo estiver jogável.

## Meta do vertical slice

Fluxo jogável de 10 a 15 minutos:

1. introdução curta;
2. fuga do tigre dente-de-sabre;
3. checkpoint e encontro na fogueira;
4. busca/coleta de um fragmento;
5. transição temporal para a próxima época.

## Inventário do que já existe

| Sistema do PDF | Estado | Local atual | Próxima entrega |
| --- | --- | --- | --- |
| Movimento e câmera 3D | Protótipo | `_testes/parkour/` | consolidar o script duplicado |
| Parkour/coleta/HUD | Protótipo | `_testes/parkour/` | transformar engrenagem em coletável genérico |
| Morte e reinício | Protótipo | `_testes/parkour/` | adicionar checkpoint atualizável |
| Inventário | Protótipo | `_testes/inventario/` | definir API de item e capacidade mínima |
| Diálogo | Plugin instalado | `addons/dialogic/` | criar conversa da fogueira |
| Transição de cenas | Integrado | `scenes/Transicao.*` | usar na viagem temporal |
| Progresso de fases | Persistência básica | `FaseCore.gd` | incluir checkpoints e estado de missão |
| Canoa | Protótipo | `_testes/mecanicaCanoa/` | adiar para “Rota das Canoas” |
| Questionário/carta | Protótipos | `_testes/questionario/`, `_testes/carta/` | avaliar uso contextual, sem interromper o loop |
| Missões/objetivos | Ausente | - | implementar objetivo ativo simples |
| IA perseguidora | Ausente | - | protótipo do tigre em rota controlada |
| Sobrevivência | Ausente | - | adiar até o loop de exploração funcionar |

## Ordem recomendada

### Marco 1 - Base estável

- [x] Corrigir reconhecimento do jogador por grupo.
- [x] Corrigir coleta e retorno de pausa.
- [x] Impedir transições duplicadas e validar caminhos.
- [x] Corrigir bloqueio/desbloqueio do menu de fases.
- [x] Salvar e carregar a conclusão das fases.
- [ ] Consolidar os dois scripts de jogador.
- [ ] Criar uma cena de teste que percorra menu, fase e retorno sem erros.

### Marco 2 - Fuga jogável

- [ ] Criar `Checkpoint3D` reutilizável.
- [ ] Criar perseguidor simples com `NavigationAgent3D` ou rota scriptada.
- [ ] Adicionar gatilhos de início/fim da perseguição.
- [ ] Exibir objetivo atual no HUD.
- [ ] Reiniciar rapidamente no último checkpoint.

Critério de pronto: o jogador conclui a fuga ou morre e reinicia sem recarregar
manualmente o projeto.

### Marco 3 - Fogueira e narrativa

- [ ] Criar diálogo curto no Dialogic.
- [ ] Bloquear movimento durante diálogo/cutscene.
- [ ] Restaurar câmera e controles ao terminar.
- [ ] Registrar a conclusão da etapa da missão.

### Marco 4 - Busca do fragmento

- [ ] Promover o coletável para um componente genérico.
- [ ] Integrar inventário mínimo de itens-chave.
- [ ] Criar puzzle/interação simples com o fragmento.
- [ ] Mostrar uma entrada histórica contextual.

### Marco 5 - Viagem temporal

- [ ] Criar efeito visual/sonoro de transição.
- [ ] Trocar de mapa mantendo o estado necessário.
- [ ] Salvar checkpoint e progresso.
- [ ] Validar o vertical slice completo.

## Depois do vertical slice

Somente após esses marcos, iniciar os sistemas de maior custo do PDF:
sobrevivência, crafting, canoa/correnteza, reputação, facções, diplomacia,
stealth, consequências históricas e códice completo.

## Checklist de validação por entrega

- A cena abre sem erros de parser ou recursos ausentes.
- Teclado e controle não disparam a mesma ação duas vezes.
- Pausa, retorno ao menu e transição funcionam.
- O sistema não depende do nome literal de um nó.
- Caminhos de recursos continuam válidos.
- A alteração é testada na cena isolada e no fluxo iniciado pela tela inicial.
