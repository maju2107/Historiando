# Estrutura do projeto

## Objetivo

Organizar o repositório aos poucos, sem mover recursos que já são referenciados
por cenas do Godot. Caminhos `res://` são parte dos arquivos `.tscn`, `.tres` e
`.gd`; uma reorganização em massa pode quebrar o projeto.

## Estrutura-alvo

```text
addons/                 plugins de terceiros
assets/
  audio/
  models/
  textures/
common/
  characters/
  fonts/
  shaders/
docs/
scenes/
  autoload/             estado global, transição e serviços
  ui/                   telas, HUD e componentes
  gameplay/
    player/
    interaction/
    inventory/
    missions/
  acts/
    megafauna/
tests/                  testes automatizados futuros
prototypes/             experimentos executáveis e descartáveis
```

Essa é uma direção, não uma migração imediata. Os nomes atuais permanecem
válidos enquanto os protótipos são avaliados.

## Regra para promover protótipos

1. Escolher um protótipo em `_testes/` que atenda a um item do vertical slice.
2. Remover duplicações e dependências específicas da cena de teste.
3. Criar uma cena reutilizável dentro de `scenes/gameplay/`.
4. Atualizar referências pelo editor do Godot, para preservar UIDs.
5. Executar a cena isolada e o fluxo completo desde a tela inicial.
6. Só então remover o protótipo antigo em outro commit.

## Convenções

- Pastas e arquivos novos: `snake_case`, sem espaços ou acentos.
- Classes e nós: `PascalCase`.
- Funções, sinais e variáveis: `snake_case`.
- Use grupos para capacidades (`player`, `interactable`, `collectible`), não o
  nome literal do nó.
- Prefira referências exportadas, grupos ou `get_viewport().get_camera_3d()` a
  caminhos rígidos longos como `$"../../Player/Camera"`.
- Cada sistema deve funcionar em uma cena de teste pequena antes da integração.
- Não versionar `.godot/`, arquivos `.tmp`, backups `.blend1` ou saídas locais.

## Dívida técnica já identificada

- Existem dois scripts quase idênticos para o jogador de parkour.
- `godot-4-3D-Characters-main/` contém um projeto de exemplo completo dentro do
  projeto principal; os assets efetivamente usados devem ser separados antes de
  removê-lo.
- Há backups e arquivos temporários já rastreados pelo Git. Eles devem ser
  revisados individualmente antes de serem removidos.
- Os protótipos de inventário, carta, questionário, canoa e parkour ainda usam
  padrões diferentes de nomes e referências.
- O save atual cobre apenas a conclusão das três fases; checkpoints, inventário
  e estado de missão ainda não são persistidos.
