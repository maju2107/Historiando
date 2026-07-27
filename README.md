# Historiando

<img src="assets/texture/logo.png" alt="Título do projeto: Historiando" width="300"/>

Jogo educacional desenvolvido em Godot sobre história e culturas dos povos
originários, com exploração, narrativa e viagem temporal.

## Estado atual

O projeto está em pré-produção/prototipagem. A prioridade definida no documento
de mecânicas é montar um **vertical slice da introdução na Megafauna** com:

- movimento e câmera em terceira pessoa;
- parkour e perseguição;
- interação e coleta;
- missão e HUD simples;
- diálogo/cutscene;
- checkpoint, morte e reinício.

Consulte [docs/ROADMAP.md](docs/ROADMAP.md) para ver o que já existe e a ordem
recomendada de implementação.

## Abrindo o projeto

1. Instale uma versão do Godot compatível com a indicada em `project.godot`.
2. Importe a pasta raiz pelo gerenciador de projetos.
3. Aguarde a importação dos assets.
4. Execute o projeto com `F6`/`F5`.

O projeto atualmente declara recursos do Godot **4.7**. Evite salvar o projeto
com uma versão anterior, pois isso pode reescrever cenas e imports.

## Organização

- `scenes/`: fluxo principal, menus e fases integradas;
- `_testes/`: protótipos isolados ainda não promovidos ao jogo principal;
- `assets/`: texturas, modelos, música e demais fontes de arte;
- `common/`: recursos compartilhados, fontes, shaders e personagens;
- `addons/`: plugins de terceiros;
- `docs/`: decisões de arquitetura, inventário de sistemas e roadmap.

As regras para promover um protótipo sem quebrar caminhos estão em
[docs/ESTRUTURA_DO_PROJETO.md](docs/ESTRUTURA_DO_PROJETO.md).

## Créditos e fontes

### Música da tela principal

Music from [Uppbeat](https://uppbeat.io/t/ian-aisling/empty-moon), por Ian
Asling. License code: `DCE7CZUFG7737NVB`.

### Carta sobre o período Pleistoceno

FERNANDES, Afonso Henrique Menezes. *Museu de Curiosidades #3 - Megafauna*.
Museu Nacional - SAE. Acesso em 22 de setembro de 2025.
