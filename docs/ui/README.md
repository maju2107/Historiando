# Interface Historiando / Pindorama

Direção escolhida: equilíbrio entre a identidade existente e HQ/arcade.
Roxo profundo `#1A002C`, creme `#DAC7A7`, ocre `#DDA63B`, terracota `#CE6035`
e verde `#2F5143`; botões recortados, sombras sólidas e retículas discretas.

## Abrir e testar

1. Abra o projeto em Godot 4.7.1 e pressione **F5**: a tela inicial já usa a interface.
2. **Começar a jornada** abre os três capítulos. O cartão grande **01 — A ilha de
   Pindorama** agora abre a ilha, identificada como **Protótipo 3D**. O botão extra
   foi removido. Os capítulos 02 e 03 preservam os caminhos e bloqueios de `FaseCore`.
3. **Créditos**, no início, substitui o botão Conhecer a HUD e reúne autores,
   fontes e links dos oito registros de assets em `Licencas_Assets`.
4. A demonstração com coleta e vidas simuladas continua disponível ao abrir
   `scenes/ui/hud_demo.tscn` e executar com **F6**.
5. **Esc** pausa/retoma; setas, Tab e Enter navegam. Os botões nativos também aceitam
   o controle configurado no Input Map; a ação `menu` existente é preservada.
6. Ajustes de volume, mudo, tela cheia e animação são guardados em
   `user://interface.cfg`, separado do progresso das fases.

## O que está integrado

- Tela inicial, seleção de capítulos, ajustes, créditos e pausa global.
- Confirmações de saída/retorno e avisos usam painéis de HQ, com fundo escurecido,
  foco inicial no cancelamento, navegação contida e restauração do foco ao fechar.
  Escape fecha a confirmação sem sair do jogo ou desfazer a pausa.
- A ilha continua sendo protótipo: esta troca de acesso não implementa conclusão
  de capítulo nem muda o progresso salvo das fases posteriores.
- HUD de vidas e coleta nos jogadores que usam `HUD/gear_container`; esse adaptador
  mantém os métodos existentes `update_gear` e `update_life`.
- Os itens existentes são apresentados como **fragmentos**. Nenhum novo sistema
  de coleta, missão, inventário ou persistência de itens foi criado.
- Ao chegar a zero vidas pelo adaptador, abre a tela **Tentar novamente**.
  Reiniciar recarrega a cena atual; não restaura um checkpoint salvo.
- Pausa restaura o modo anterior do mouse e não abre sobre os menus principais.
- O protótipo de parkour delega a pausa ao autoload, evitando menus duplicados.
- Objetivos e dicas de interação têm API pública, mas sua atualização por missões
  e NPCs ainda depende dos sistemas de gameplay. A demonstração identifica os
  valores de exemplo; o cenário usa a orientação genérica de exploração.

## Componentes

| Arquivo | Finalidade |
| --- | --- |
| `scenes/ui/interface.tscn` e `interface.gd` | Telas compartilhadas, construídas em código |
| `scenes/ui/historiando_hud.tscn` | HUD reutilizável; adicionar sob um CanvasLayer |
| `scenes/ui/comic_button.gd` | Button nativo com desenho próprio e estados de foco |
| `scenes/ui/comic_backdrop.gd` | Paisagem vetorial original e retícula |
| `scenes/ui/halftone.gd` | Pontos alternados, variação estável e bordas suaves |
| `scenes/ui/comic_panel.gd` | Painéis de avisos e notificações |
| `scenes/ui/credit_data.gd` | Autores, links e licenças extraídos do registro |
| `scenes/ui/ui_kit.gd` | Paleta, fontes, marca e helpers |
| `scenes/ui/pause_manager.gd` | Pausa global e tela de nova tentativa |
| `common/fonts/historiando/` | Fontes, licenças e script da fonte derivada |

A composição usa uma área lógica de 1600 × 900, escalada uniformemente e centrada.
Em outras proporções, preserva a composição com margens; não é um layout móvel
em retrato. Os nós são criados em execução: para alterar a composição, editar as
coordenadas em `interface.gd`; executar F6 para ver o resultado.

API da HUD:

```gdscript
hud.set_health(2, 3)
hud.set_collectibles(5)
hud.set_objective("Encontre o caminho até o rio.")
hud.set_interaction("Conversar", "E")
hud.set_interaction("") # esconde a dica
hud.notify("NOVA DESCOBERTA!")
```

## Arte e tipografia

As marcas em tela agora usam os SVGs originais fornecidos pelo usuário:

- `brand_group_28.svg`: **Group 28.svg**, marca colorida na tela inicial.
- `brand_symbol.svg`: **espiral guarana2.0 amarela.svg**, símbolos da HUD e menus.
- `brand_wordmark.svg`: **Vector.svg**, assinatura dos rodapés.

Os SVGs foram copiados sem alterar os desenhos. São importados em escala 3×,
com mipmaps para manter nitidez nas diferentes escalas da interface. O PNG
`brand_board.png` permanece apenas como referência original; não é mais usado em tela.
O `a` do usuário está preservado em `a_reference.png`. A paleta parte de **Frame 2.png**.
As quatro referências externas serviram apenas para direção visual: nenhuma de
suas imagens foi adicionada à interface. Paisagem, portal, formas, retícula e
ícone do slider são desenhos originais feitos em código/vetor. O portal é um
elemento de fantasia, não uma representação de um artefato histórico.

Historiando Mosaico é uma **primeira derivação**, com `a` reconstruído e acentuação
portuguesa, não uma família tipográfica totalmente original. Consulte o README
e as licenças em `common/fonts/historiando/`.

## Verificação

Os créditos são extraídos, sem modificar a planilha, por
`python scenes/ui/build_credits.py`. A fonte é o arquivo
`assets/models/Licencas_Assets/Registro_de_Licencas_Assets_ATUALIZADO.xlsx`, primeira
aba, linhas 5–12. Usa-se esse registro atualizado (CC BY 4.0 para Creative Trio e
CC0 para Kenney), não o LEIA-ME antigo que ainda descreve Standard/Royalty Free.
O resultado inclui a linha de origem e é incorporado ao jogo como GDScript,
sem depender da presença do XLSX no executável exportado.

Executar a partir da raiz, substituindo `godot` pelo executável local:

```powershell
godot --headless --path . --script res://scenes/ui/verify_ui.gd
godot --headless --path . --script res://scenes/ui/verify_gameplay_ui.gd
```

Para refazer as imagens das telas com renderização real:

```powershell
godot --path . --script res://scenes/ui/verify_ui.gd -- --capture
godot --path . --script res://scenes/ui/verify_gameplay_ui.gd -- --capture
```

Os testes cobrem navegação, bloqueios conforme o save existente, vidas/coleta,
pausa por Escape, restauração de cursor, nova tentativa, carregamento dos três
capítulos e retorno ao início. Não alteram o progresso salvo.
Também são verificados os oito registros dos créditos, confirmação/cancelamento,
restauração de foco e o acesso real à ilha pelo cartão 01. Controle físico
não foi testado. As imagens `01` a `12` são capturas do Godot em Forward+, como o
projeto. Os testes de comportamento também passaram em Compatibility; esse backend
apresentou capturas parciais ao rolar conteúdo, então a revisão visual final foi
feita em Forward+.

A importação geral do repositório ainda relata falha em um asset preexistente
`rock_m.fbx`; o carregamento das cenas testadas funcionou. O backend headless
também pode emitir avisos de recursos ao encerrar; a verificação renderizada da
interface e do gameplay encerrou sem esses erros.
