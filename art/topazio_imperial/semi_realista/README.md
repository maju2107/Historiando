# Topázio imperial — versão semi-realista

Revisão do cristal cartoon aprovado, criada no Blender instalado neste computador. Mantém o corpo e a paleta mel/laranja e acrescenta lascas reais na malha, assimetrias nas faces, microchanfros, estrias de crescimento, fissuras finas, inclusões e variação de polimento.

- `topazio_imperial_semi.blend`: modelo editável com as três texturas empacotadas; a coleção `STUDIO` contém somente o cenário dos renders.
- `topazio_imperial_semi.glb`: uma malha e um material PBR; mapas de cor, normal e rugosidade embutidos, de 2048 × 2048 pixels.
- `topazio_imperial_prop.tscn`: cena opcional com colisão convexa simples.
- `topazio_imperial_semi_preview.png`, `topazio_imperial_semi_back.png` e `topazio_imperial_semi_detalhe.png`: renders de inspeção.
- `manifest.json`: dimensões, contagens, hashes e verificações.

O material usa normal map para as irregularidades pequenas e geometria para as lascas. O cristal continua opaco: o aspecto interno é sugerido pela textura e pelo brilho, sem refração. A aparência no jogo depende da iluminação. A colisão simples conserva o contorno geral, sem reproduzir cada lasca.

Para importar no Godot, copie o GLB e a TSCN juntos para uma pasta dentro de `assets/`, aguarde a importação e arraste a cena para o cenário. A pasta `art/` é ignorada pelo importador do projeto. Pivô na base e escala em metros, com aproximadamente 0,74 m de altura.

Geometria e mapas procedurais originais. As três fotos fornecidas orientam forma e cor; seus pixels não são usados como textura. Licença MIT, conforme `LICENSE.txt`.

Gerador: `tools/topazio_imperial/refine_topazio.py`; depende do arquivo Blender cartoon original, preservado na pasta superior.
