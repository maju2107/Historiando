# Refinamento do seu FBX

**Atualização de 01/10/2026:** a versão atual recupera os olhos alongados e a mão com três dedos mais polegar, inclui retopologia e esqueleto. Abra [character_GAME_RIGGED.blend](output/character_GAME_RIGGED.blend) e leia [GAME_README.md](GAME_README.md). O conteúdo abaixo documenta a entrega anterior, preservada como histórico.

Arquivo de entrega: [output/character_FINAL.blend](output/character_FINAL.blend).

O trabalho parte exclusivamente de `source/base.fbx`, a cópia do arquivo que você modelou. O projeto anterior gerado do zero não foi usado como geometria. Os checkpoints numerados e suas revisões foram mantidos em `output/`.

## O que foi preservado e alterado

- Corpo contínuo, cabeça, pescoço, orelhas, olhos, pálpebras, pés e dedos existentes foram mantidos e remodelados pelas posições dos vértices. A cabeça não foi substituída.
- Proporções ajustadas pelas vistas frontal e lateral: crânio mais largo, olhos maiores e mais próximos, pernas alongadas, cintura e quadril ajustados, pés largos e alcance dos braços reduzido.
- A curvatura original das bochechas foi recuperada e a transição abaixo dos olhos foi suavizada. Nariz e boca mantêm a estrutura original, com redução localizada.
- A origem tinha três dedos longos e um polegar por mão. Foi acrescentado o quarto dedo longo, substituindo somente oito faces da palma e acrescentando 97 vértices no lado editado; o Mirror produz o outro lado. Os dedos originais foram preservados.
- Sobrancelhas novas foram acrescentadas. As orelhas originais, incluindo seus relevos internos, foram preservadas.
- O bloco retangular auxiliar do quadril foi arquivado em `SOURCE_PARTS`; havia uma pelve contínua sob ele. A malha anterior à inserção do dedo também está arquivada.
- A cabeça e outros componentes conservam a forma importada normalizada em uma shape key inativa. O checkpoint 01 e o FBX guardam a importação original completa.

## Conferência visual

- [Referência × refinamento: frente e lateral](renders/comparison_front_side.png)
- [Referência × refinamento: costas e 3/4](renders/comparison_back_three_quarter.png)
- [Seu FBX antes × depois](renders/before_after.png)
- [Rosto](renders/face_closeup.png), [rosto em 3/4](renders/face_three_quarter.png), [mão vista de cima](renders/hand_after.png)
- [Topologia real do rosto](renders/topology_face.png), [corpo](renders/topology_front.png), [mão](renders/topology_hand.png)

As comparações usam alturas equivalentes. A referência lateral foi espelhada para acompanhar a direção da câmera. A vista 3/4 tem enquadramento aproximado; não é uma coincidência pixel a pixel. A imagem do FBX original usa iluminação diferente e oculta apenas seu bloco auxiliar de quadril.

As nove imagens foram classificadas, copiadas sem alterar os originais e incorporadas ao `.blend`. As vistas frontal, lateral e traseira definem dimensões; os closes não foram tratados como vistas ortográficas. A proporção medida nas imagens é aproximadamente 2,76 cabeças de altura.

## Medidas e limites

O modelo está em metros, voltado para **−Y**, centrado em X=0, com altura avaliada de aproximadamente 1 m e sola em Z=0. Transformações dos objetos de personagem são identidade.

| Medida frontal | Referência aproximada | Modelo |
|---|---:|---:|
| Largura da cabeça em Z=0,82 m | 348,7 mm | 344,8 mm |
| Cintura em Z=0,48 m | 127,6 mm | 127,0 mm |
| Quadril em Z=0,39 m | 192,0 mm | 190,0 mm |
| Largura externa dos dois pés em Z=0,025 m | 302,6 mm | 302,8 mm |
| Diâmetro dos olhos | 85,1 mm | 85,0 mm |
| Distância entre centros dos olhos | 153,1 mm | 153,1 mm |

Dados completos: [proportion_comparison.json](output/proportion_comparison.json).

**A topologia original é densa.** Foi preservada por prioridade à autoria e à geometria aproveitável do FBX. O resultado é predominantemente composto de quads, mas não reproduz a contagem ou a posição individual das arestas econômicas da referência. Redução por un-subdivide foi testada e rejeitada por danificar a organização da malha. Não há remesh, reconstrução integral, rig ou pesos de deformação entregues.

Cabeça, pescoço e corpo permanecem componentes separados, como na origem, com sobreposição nas junções. As orelhas, pálpebras e olhos também são peças separadas. O visual conserva características suas, especialmente pálpebras, orelhas, mãos e boca; não se trata de uma cópia exata da referência.

## Organização no Blender

- `CHARACTER`: partes editáveis. Mirror e Subdivision na cabeça, corpo e pescoço.
- `REFERENCES`: imagens incorporadas, coleção desativada.
- `SOURCE_PARTS`: peças de segurança, coleção desativada.
- `VALIDATION`: câmeras ortográficas de frente, lado direito, costas, 3/4 e closes; iluminação.
- `TOPOLOGY_REVIEW`: cópias auxiliares dos contornos reais das faces, desativadas. Não fazem parte da geometria do personagem.

O material cinza e as câmeras estão prontos para inspeção. UVs importadas foram mantidas; componentes que não tinham UV receberam projeção automática de apoio, sem promessa de UV final para texturização.

## Verificações e continuidade

Os relatórios de entrega verificam malha de controle e subdividida: arestas não manifold, orientação das normais, faces degeneradas, vértices coincidentes e simetria das partes centrais. O teste de autointerseção geométrica cobre cabeça, corpo e pescoço individualmente; não representa uma prova de ausência de sobreposição entre componentes separados.

Os relatórios definitivos da reabertura são `output/validation_reopened_control.json`, `output/validation_reopened_subdivision.json` e `output/delivery_manifest.json`.

Para continuar, abra `output/character_FINAL.blend` ou o arquivo indicado em `progress.json`. **Não reimporte o FBX e não execute novamente os marcos anteriores sobre a versão atual.** Os scripts de revisão indicam explicitamente qual checkpoint recebem; suas deformações não são cumulativas nem idempotentes. `scripts/config.py` guarda os parâmetros principais e `scripts/helpers.py` as funções de salvamento/render. Os scripts Python também estão incorporados ao `.blend` como textos.
