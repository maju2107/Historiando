# Chibi feminina — referências de 17/09

Abra **Chibi_Feminina.blend** no Blender. O modelo foi reconstruído a partir das nove imagens de 1400 × 1000 pixels fornecidas, comparando as vistas frontal, lateral, traseira e os detalhes do rosto.

A construção reproduz a cabeça grande, olhos redondos, pálpebras, dois cílios por olho, sobrancelhas arqueadas, nariz pequeno, boca com abertura, orelhas com cavidade, pose T e pernas que se alargam em direção aos pés. As mãos têm três dedos longos e um polegar, seguindo a mão estilizada visível na referência superior. Top e peça inferior são objetos separados, como na prancha original.

É uma reconstrução visual; a posição de cada aresta não é uma recuperação exata do arquivo original.

## Arquivos

- **Chibi_Feminina.blend** — projeto editável, com estúdio, câmera e nove referências empacotadas.
- **Chibi_Feminina.glb** — modelo com a superfície subdividida, para importar em Godot e outros aplicativos.
- **Chibi_Feminina.obj** + **.mtl** — malhas de controle em quads, com UVs.
- **preview.png** — seis vistas do resultado.
- **comparacao.png** — referência frontal e reconstrução lado a lado.
- **front.png**, **side.png**, **back.png**, **three_quarter.png** — vistas do corpo.
- **face_front.png**, **face_three_quarter.png** — detalhes do rosto.
- **clay.png** — render sem linhas de topologia.
- **hand_detail.png** e **top_three_quarter.png** — detalhe da mão e vista elevada, gerados por `render_details.py`.
- **validation.json** — verificações do projeto salvo.

## Editar

O corpo, a cabeça, o nariz, a boca e as orelhas formam uma superfície contínua: **2.320 quads e 2.322 vértices**. O conjunto completo contém **3.322 faces de controle** em 13 objetos de malha. A subdivisão Catmull–Clark de nível 2 permanece como modificador editável; os detalhes de roupa e pálpebras também mantêm seus modificadores de espessura.

Use **Tab** para editar o objeto selecionado. Os grupos de vértices identificam as regiões do corpo e do rosto. `Character_Root` move o conjunto inteiro. O top e a peça inferior podem ser ocultados no Outliner. Os olhos mantêm o acabamento cinza sem textura da referência.

Frente: **-Y**. Vertical: **Z**. Altura aproximada: **3,6 unidades**. Todas as malhas têm UVs. O personagem ainda **não possui rig nem animações**.

As linhas das prévias estão em uma curva separada dentro da coleção de estúdio, ocultada no viewport e excluída das exportações. As imagens de referência estão na coleção oculta e no Image Editor. A pasta tem `.gdignore`; copie o GLB para a pasta de assets quando quiser importá-lo no projeto Godot.

## Verificação e reprodução

Criado e reaberto no Blender 5.2.1 LTS. A validação verifica a conectividade, simetria, faces quad, áreas não degeneradas, ausência de arestas abertas e de interseções entre faces não adjacentes no corpo/cabeça, antes e depois da subdivisão. Confere também os UVs, o fechamento das demais peças após os modificadores e as nove imagens empacotadas. A exportação GLB é reimportada em uma cena temporária para verificar as 13 malhas, os UVs e os materiais.

Na revisão de topologia de 20/09, a cabeça foi reconstruída com 32 colunas e um topo em grade de quads, eliminando a concentração de arestas em um polo. Os contornos dos olhos passaram de 26 para 16 segmentos, com aberturas mais circulares. As pernas têm divisões distribuídas ao longo da coxa e da panturrilha, com pequenos desvios de fluxo nas laterais dos joelhos. A ponte de separação entre as pernas foi preservada. O punho e a palma foram arredondados na própria malha de controle; os pés, a testa, o nariz, a boca e a implantação das orelhas também foram ajustados.

As linhas dos renders acompanham duas etapas reais de subdivisão, mantendo a densidade de arestas da malha de controle. A espessura das roupas é considerada no posicionamento dessas linhas. A versão anterior e sua comparação estão em **previous/**, para consulta.

```text
blender --background --threads 6 --python-exit-code 1 --python build_character.py
blender --background --threads 6 --python-exit-code 1 --python validate_character.py
```

O gerador usa `base_geometry.py` para as conexões do corpo, `reference_head.py` para a cabeça, `refine_body.py` para as pernas, `refine_arms.py` para braços e mãos e `smooth_preview.py` para as linhas da prévia. Esses módulos estão incluídos como textos no `.blend`. A geração sobrescreve os arquivos desta pasta; salve edições manuais com outro nome antes de executar novamente. `-- --no-render` pula os renders; `-- --quick` gera quatro vistas menores para inspeção. `make_preview.ps1` monta as pranchas usando os PNGs gerados. Execute `render_details.py` no Blender para atualizar as duas vistas adicionais.
