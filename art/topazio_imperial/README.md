# Topázio imperial cartoon

Prop original modelado com Blender a partir da forma e das cores das três fotos fornecidas. Corpo alongado de seção retangular com cantos chanfrados, terminação oblíqua e estrias discretas. As fotos não foram utilizadas como textura.

- `topazio_imperial.blend`: arquivo editável, com textura empacotada. A coleção `PROP` contém o cristal; `STUDIO` contém somente câmera, luzes e chão da prévia.
- `topazio_imperial.glb`: modelo para importar no jogo, com material PBR e textura embutida. Não contém o estúdio.
- `topazio_imperial_prop.tscn`: cena opcional do Godot com o GLB e uma colisão convexa simples.
- `topazio_imperial_basecolor.png`: textura de cor de 1024 × 1024 pixels.
- `topazio_imperial_preview.png`, `topazio_imperial_front.png` e `topazio_imperial_back.png`: renders de inspeção.
- `manifest.json`: contagens, dimensões, procedência, verificações e hashes dos arquivos.

Para usar no Godot, copie o GLB e a cena TSCN juntos para uma pasta dentro de `assets/` e aguarde a importação. Arraste a cena TSCN para o cenário para ter colisão, ou arraste só o GLB para ter apenas o visual. Esta pasta de autoria fica sob `art/.gdignore`; portanto, o Godot não importa seus arquivos diretamente daqui.

Escala em metros, aproximadamente 0,75 m de altura. O pivô fica no centro da base; é possível reduzir o prop uniformemente no editor. Um único material opaco, com estrias e gradiente pintados para sugerir cristal sem depender de transparência. O brilho depende da iluminação do jogo. Sem rig ou animações.

Verificação: 338 vértices e 672 triângulos; malha fechada, sem arestas não manifold. GLB e TSCN importados e instanciados em um projeto isolado no Godot 4.7.1, com material, textura e colisão convexa de 32 pontos. Os renders de prévia foram feitos no Blender 5.2.2 LTS instalado neste computador.

Licença: MIT, conforme `../../LICENSE`, incluída também em `LICENSE.txt`. Não há geração paga nem imagens de terceiros incorporadas ao material.

Gerador reproduzível: `tools/topazio_imperial/create_topazio.py`. Execute com Blender em modo background, a partir de uma instalação que aceite argumentos de linha de comando.
