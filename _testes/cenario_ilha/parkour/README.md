# Parkour flutuante e controles da ilha

Abra `res://_testes/cenario_ilha/CenarioIlha.tscn` e execute a cena com **F6**.

## Trocar teclado/controle por fliperama

Durante o jogo, abra **Pausa → Ajustes → Controles** para escolher **Teclado /
Joystick**, **Fliperama** ou **Mobile**. A troca é aplicada ao jogador atual e
salva para as próximas sessões; o seletor de desenvolvimento foi removido da HUD.
No modo Mobile, o joystick circular inferior esquerdo controla a direção e a
intensidade do movimento; o botão inferior direito pula. Arraste outro dedo
fora desses controles para girar a câmera. Os três gestos podem ser usados
simultaneamente. A sensibilidade e a inversão vertical usam as opções de
**Camera Livre**. Os controles se ajustam ao tamanho da tela.

1. Na árvore de `CenarioIlha`, selecione **Player**.
2. No Inspector, vá a **Controles → Control Preset**.
3. Escolha **Teclado e Controle** (padrão) ou **Fliperama** e salve a cena.

| Modo | Movimento | Câmera | Pulo |
| --- | --- | --- | --- |
| Teclado e Controle | WASD/setas ou analógico esquerdo/direcional, em relação à câmera | Mouse ou analógico direito, com órbita livre | Espaço ou A / botão inferior do controle |
| Fliperama | Direcional ou WASD/setas; mantém a direção enquanto estiver pressionado | Acompanha o personagem automaticamente | Espaço ou botão mapeado em `ui_accept` |

No modo livre, **Esc** abre a pausa e **clique esquerdo** captura novamente.
Em **Camera Livre**, ajuste `Mouse Sensitivity`, `Joystick Sensitivity`,
`Camera Stick Deadzone` e `Invert Camera Y`. Em **Camera de Fliperama**, ajuste
`Follow Pitch Degrees` e `Camera Turn Speed`. As configurações de ambos os modos
ficam guardadas; basta trocar `Control Preset`, sem editar o script.

Para mapear os botões físicos do fliperama, use **Projeto → Configurações do Projeto
→ Mapa de Entrada**: `ui_left`, `ui_right`, `ui_up`, `ui_down` e `ui_accept`.
O projeto usa o controle de índice 0 para os direcionais e analógicos.

## Percurso

São 21 plataformas sem texto no piso na **Trilha dos céus**. O início fica próximo ao
spawn, segue para leste e sobe 55 cm por salto, completando uma volta acima da
ilha. O percurso foi aproximado para funcionar com o pulo atual da ilha
(`Jump Velocity = 5`, `Walk Speed = 6.5`). Setas no piso indicam o próximo salto.
As superfícies continuam translúcidas, com ondulações mágicas discretas, linhas
finas e bordas luminosas em ocre. Durante a fase fantasma, resta um contorno
tracejado fraco, sem piso nem colisão.

Na ilha, cada plataforma comum fica **8 s sólida** e **2 s sem colisão**. As
plataformas vizinhas têm uma diferença de **1 s** entre seus ciclos, próxima do
tempo de um salto. A borda frontal indica o tempo restante e o brilho muda para
vermelho e pulsa nos últimos **1,2 s** antes de desaparecer.
O relógio é contínuo e não depende de pisar nelas: espere a janela do ciclo para
começar. As plataformas **01, 08, 15 e 21** são maiores e permanecem sólidas:
o brilho verde e os cristais flutuantes identificam os pontos seguros entre as
três etapas. Elas também continuam transparentes.

Pisar em um ponto verde atualiza o retorno do jogador durante esta sessão.
O jogador mede a distância entre o ponto mais alto em que esteve no ar e o chão
onde pousou. Quedas de até **8 m** são seguras: é possível cair das primeiras
plataformas e continuar explorando. Uma queda maior desconta **uma vida** e
retorna ao último checkpoint. Ajuste esse limite em **Player → Retorno → Fall
Damage Height**. A altura é reiniciada em cada pouso: descer os níveis normais
da ilha não acumula dano, mesmo depois de visitar um checkpoint.
A próxima sequência recebe uma janela sólida nova. A imunidade evita outro
desconto de vida, mas não impede o retorno em outra queda alta. Ao chegar a zero
vidas, a tela global permite reiniciar. A ilha não usa volumes de morte:
`Fall Reset Height = -8 m` protege apenas contra quedas para fora do mundo,
onde não existe chão para detectar o impacto.

A trilha não usa títulos flutuantes; a mensagem de início aparece na HUD.
A HUD mostra os saltos alcançados, confirma pontos de retorno e celebra a chegada
ao mirante. A conclusão é local a esta cena; não desbloqueia capítulos nem grava
progresso permanente.

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
dos ciclos. `Checkpoint` marca pontos de retorno e aplica a aparência verde;
mantenha `Permanent` ligado nesses pontos e na plataforma final. As setas apontam
para o eixo local **-Z**: ao mover plataformas, ajuste a rotação em Y para o
próximo salto.

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
plataforma final permanente. Também são verificados pousos nos pontos de retorno,
recuperação com desconto de uma vida, imunidade a dano e conclusão na HUD.
O script `_validate_respawn.gd` verifica exploração e descidas entre níveis da
ilha antes/depois dos checkpoints, quedas seguras das duas primeiras plataformas,
queda alta com retorno ao checkpoint, limite de dano, altura do ápice, retorno fora
da ilha, imunidade e duas novas tentativas consecutivas.
O teste orienta a base da câmera para cada salto; não substitui uma sessão com
um controle físico. Os controles são verificados com eventos simulados
de teclado e joystick, além da órbita do mouse e da troca de preset.

Para revisar a aparência real em Forward+, execute
`godot --path . --windowed --script res://_testes/cenario_ilha/_preview_parkour.gd`.
As capturas da entrada, percurso, ponto de retorno, aviso e fase fantasma ficam
em `tmp/parkour/`, ignorado pelo Git.
