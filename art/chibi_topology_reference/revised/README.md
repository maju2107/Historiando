# Topologia corrigida

Abra **Chibi_Topology_Corrigida.blend**. Esta versão aplica as três novas referências à base do personagem.

- **Mãos:** cinco dedos separados por mão, polegar integrado à palma, membranas entre os dedos, loops nas articulações e pontas arredondadas em quads. Grupos de vértices permitem selecionar cada dedo.
- **Joelhos:** área da patela com seis quads, cercada por um loop fechado de dez quads. Os loops têm mais espaço na frente e menos espaço na dobra posterior.
- **Virilha:** ponte com oito quads, distribuídos em duas colunas entre as raízes das pernas. As pernas têm contornos próprios e não se encontram em um único vértice.

A malha mantém a altura e as proporções gerais da base. Passou de 805 para **1.689 quads / 3.378 triângulos / 1.691 vértices** para acomodar as novas articulações. Continua sendo uma superfície única, fechada, simétrica e com UVs. Cabeça, tronco superior, braços e pés mantêm a construção anterior.

## Arquivos

- `Chibi_Topology_Corrigida.blend`: projeto editável.
- `Chibi_Topology_Corrigida.glb`: exportação da malha em repouso para Godot e outros aplicativos.
- `Chibi_Topology_Corrigida.obj` e `.mtl`: exportação com faces quad e UVs.
- `preview_topologia.png`: visão conjunta das três correções.
- `hand_detail.png`: mão aberta com cinco dedos.
- `knee_front.png`, `knee_side.png`, `knee_bent.png`: patela, vista lateral e flexão de 60°.
- `hips_front.png`, `hips_under.png`: separação das pernas e ponte inferior da virilha.
- `front.png`, `side.png`, `back.png`, `three_quarter.png`: personagem completo.
- `validation.json`: resultados da validação do arquivo salvo.

As cores nos detalhes são marcações de revisão: roxo na patela, verde no contorno e laranja na ponte da virilha. O personagem salvo e exportado mantém o material cinza.

## Inspecionar no Blender

O personagem está selecionado na vista frontal, com arestas visíveis. Use **Tab** para editar. O modificador de subdivisão é opcional e está desligado. A coleção de estúdio contém as curvas de arestas usadas nos renders e não faz parte da malha exportada.

Em **Object Data Properties → Shape Keys**, `Teste_joelho_L_60graus` permite conferir a flexão do joelho esquerdo. Está salva com valor zero. É uma deformação de teste; o personagem ainda não possui rig ou pesos de animação. O comportamento de poses finais depende desse trabalho posterior.

A referência original e as três novas imagens estão empacotadas no `.blend`, acessíveis no Image Editor. A versão anterior continua na pasta superior.

## Validação e reprodução

Verificado no Blender 5.2.1 LTS: malha única, faces quad, simetria, ausência de arestas abertas, faces degeneradas e interseções entre faces sem vértices compartilhados. A flexão de 60° também passou pelas verificações de interseção e área das faces.

```text
blender --background --threads 6 --python-exit-code 1 --python build_model.py
blender --background --threads 6 --python-exit-code 1 --python validate_model.py
```

O gerador sobrescreve os arquivos produzidos nesta pasta. Salve edições manuais com outro nome antes de executá-lo. `-- --no-render` pula os renders; `-- --bend-only` renderiza somente a flexão. `make_preview.ps1` monta a prancha a partir dos renders.
