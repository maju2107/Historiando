# Parkour flutuante e controles da ilha

Abra `res://_testes/cenario_ilha/CenarioIlha.tscn` e execute a cena com **F6**.

## Trocar teclado/controle por fliperama

1. Na árvore de `CenarioIlha`, selecione **Player**.
2. No Inspector, vá a **Controles → Control Preset**.
3. Escolha **Teclado e Controle** (padrão) ou **Fliperama** e salve a cena.

| Modo | Movimento | Câmera | Pulo |
| --- | --- | --- | --- |
| Teclado e Controle | WASD/setas ou analógico esquerdo/direcional, em relação à câmera | Mouse ou analógico direito, com órbita livre | Espaço ou A / botão inferior do controle |
| Fliperama | Direcional ou WASD/setas; mantém a direção enquanto estiver pressionado | Acompanha o personagem automaticamente | Espaço ou botão mapeado em `ui_accept` |

No modo livre, **Esc** solta o cursor e **clique esquerdo** captura novamente.
Em **Camera Livre**, ajuste `Mouse Sensitivity`, `Joystick Sensitivity`,
`Camera Stick Deadzone` e `Invert Camera Y`. Em **Camera de Fliperama**, ajuste
`Follow Pitch Degrees` e `Camera Turn Speed`. As configurações de ambos os modos
ficam guardadas; basta trocar `Control Preset`, sem editar o script.

Para mapear os botões físicos do fliperama, use **Projeto → Configurações do Projeto
→ Mapa de Entrada**: `ui_left`, `ui_right`, `ui_up`, `ui_down` e `ui_accept`.
O projeto usa o controle de índice 0 para os direcionais e analógicos.

## Percurso

São 21 plataformas numeradas. O início fica próximo ao spawn, segue para leste
e sobe 65 cm por salto, completando uma volta acima da ilha. As bordas e os
vértices têm brilho laranja, com superfícies transparentes.

Cada plataforma comum fica **4,5 s sólida** e **2 s sem colisão**. As plataformas
vizinhas têm uma diferença de **1,25 s** entre seus ciclos, próxima do tempo de um
salto. O brilho pulsa nos últimos **0,75 s** antes de desaparecer. Durante a fase
sem colisão, o contorno fica tênue para mostrar onde ela vai voltar.
O relógio é contínuo e não depende de pisar nelas: espere a janela do ciclo para
começar. A plataforma **CHEGADA** é maior e permanece sólida o tempo todo.

No Inspector de **ParkourFlutuante**, ajuste:

- `Active Seconds` / `Ghost Seconds`: duração de cada estado.
- `Stagger Seconds`: diferença entre os ciclos das plataformas vizinhas; zero
  faz todas desaparecerem juntas.
- `Warning Seconds`: antecedência do aviso pelo brilho.
- `Cycle Enabled`: desative para praticar com todas sólidas.
- `Edge Color` / `Glow Strength`: cor e intensidade do brilho.

Para mudar o trajeto, abra `FloatingParkour.tscn`. Cada plataforma é um nó comum
que pode ser movido, rotacionado ou duplicado. Ajuste o tamanho com `Platform Size`
para atualizar a aparência e a colisão juntas. A ordem dos nós determina a ordem
dos ciclos. Mantenha `Permanent` ligado na plataforma final.

O brilho usa o Environment próprio da ilha, `island_glow_environment.tres`.
As plataformas aparecem sólidas no editor para facilitar o posicionamento.

## Verificação

Os scripts `_validate_floating_parkour.gd`, `_validate_control_presets.gd` e
`_validate_follow_camera.gd` ficam na pasta `cenario_ilha`. Execute os testes de
percurso e câmera automática com
`godot --headless --fixed-fps 60 --path . --script <caminho-do-script>`.
Para `_validate_control_presets.gd`, substitua `--headless` por `--windowed`: a
captura do mouse exige uma janela real do Godot.
O percurso é percorrido pelo controlador real em ambos os modos, com o ciclo
ligado e desligado; também são verificadas a perda/restauração de colisão e a
plataforma final permanente. Os controles são verificados com eventos simulados
de teclado e joystick, além da órbita do mouse e da troca de preset.
