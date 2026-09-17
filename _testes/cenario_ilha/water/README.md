# Água da ilha

Abra `res://_testes/cenario_ilha/CenarioIlha.tscn` e execute a cena com **F6**.
O córrego começa ao pé do mirante, passa por duas quedas com poças de impacto
e termina em uma terceira queda na borda da ilha.

O terreno e sua colisão são rebaixados juntos. O centro do leito fica 32 cm
abaixo da água; as margens têm rampas para entrar e sair andando. A água não
possui colisão: o personagem anda sobre o fundo. O modelo original dos blocos
é preservado; a escavação ocorre nas instâncias marcadas com `carve_watercourse`.

A margem é parte da malha desses blocos: `carve_watercourse.gd` subdivide a
região do córrego, `watercourse_profile.gd` define o rebaixo e `river_bank.gdshader`
aplica a cor de terra. A colisão usa a mesma malha que aparece na tela.
O recorte só alcança a camada superficial dos patamares de 4, 8 e 12 metros,
com rebaixo de 46 cm em relação ao gramado (32 cm ficam sob a água). As paredes
abaixo do leito e plataformas mais altas conservam a geometria original.
As normais de iluminação também são preservadas fora da escavação.

`Mirante` e `SacadaPicoSul` ficam fora da escavação. A nascente começa depois
do mirante e a queda superior alcança a poça à frente da sacada.
Para desativar o recorte de um bloco, selecione-o em **Terrain** e desmarque
**Carve Watercourse** no Inspector: a malha e a colisão voltam ao modelo original.

Há correnteza, variação de cor por profundidade, refração, espuma nas margens
e interseções, ondas que se expandem a partir dos passos, respingos na entrada,
espuma e névoa nos dois impactos. A última queda desaparece no vazio, sem uma
poça ou impacto artificial suspenso no ar.

## Ajustes

Selecione **Water** na cena da ilha. No Inspector:

- `Shallow Color` e `Deep Color`: cores da água rasa e mais profunda.
- `Foam Color`: cor da espuma e das linhas das quedas.
- `Flow Speed`: velocidade visual da correnteza e das quedas.
- `Refraction Strength`: distorção da imagem sob a água; zero desativa a distorção.
- `Ripple Spacing`: distância entre as ondas do rastro.
- `Interactor Group`: grupo dos personagens que interagem; padrão `player`.

Para escolher outra cor, abra `CenarioIlha.tscn`, selecione **Water**, expanda
**Agua** no Inspector e clique no quadrado de `Shallow Color`. No seletor,
escolha a cor ou digite seu código hexadecimal. A paleta atual usa **#89CFF0**
(azul bebê) em `Shallow Color`, **#4F9DD9** em `Deep Color` e **#F1FAFF** em
`Foam Color`. Salve a cena com **Ctrl+S**. As quedas acompanham essas cores.

Os valores salvos no Inspector da instância têm prioridade sobre os padrões
do script e de `IslandWater.tscn`; mudar apenas o script pode não alterar a ilha.
Para voltar ao padrão, use a seta de redefinir ao lado da propriedade.
A terra das margens usa **#E99268**, extraído da paleta original dos blocos;
esse valor fica em `bed_color` no shader `river_bank.gdshader`.

O ponto de origem do personagem deve ficar nos pés, como no Player desta cena.
As ondas são armazenadas em 24 posições fixas e somem em 2,2 segundos. A
verificação de altura impede interações em outro patamar ou acima da água.
O shader também evita refratar objetos amostrados à frente da superfície.

`watercourse_profile.gd` centraliza percurso, largura, altura e profundidade
usados pela água, pela escavação e pela interação. Para alterar o percurso,
edite esse perfil e reabra a cena para reconstruir a geometria. Mantenha `Water`
na origem da ilha; mova a raiz `CenarioIlha` para posicionar o conjunto.

Os filhos gerados são internos e reaparecem ao carregar a cena. As malhas e
os efeitos podem ser vistos no editor; a interação com o personagem roda no jogo.
A refração depende das texturas de tela/profundidade do Godot. O visual foi
conferido no renderizador **Forward+** usado pelo projeto.

## Verificação

```sh
godot --headless --path . --script _testes/cenario_ilha/_validate_water.gd
```

O teste verifica a profundidade por raycasts, a travessia com a colisão real do
Player, entrada, movimento, salto, saída, expiração das ondas, remoção do
personagem e deslocamento da ilha. O teste existente `_validate_scene.gd`
também cobre o carregamento da ilha e da vegetação.
Também compara as colisões com uma cópia sem escavação para detectar rebaixos
excessivos ou deformação das plataformas, e verifica se as quedas atravessam
algum bloco do terreno.

## Referências

- [Minions Art — Interactive Water](https://www.patreon.com/minionsart/posts/shader-graph-30490169): profundidade, refração, espuma de interseção e rastros.
- [Referência visual de cachoeira indicada](https://www.youtube.com/watch?v=25kwDu3OPmM).
- [Godot — Screen-reading shaders](https://docs.godotengine.org/en/stable/tutorials/shaders/screen-reading_shaders.html).

Implementação própria em GDScript e shaders espaciais; não requer Shader Graph,
texturas externas nem arquivos pagos dos tutoriais.
