# Personagem para animação — olhos e mãos originais recuperados

Abra **`output/character_GAME_RIGGED.blend`**. Esta é a versão nova solicitada em 01/10/2026. O antigo `character_FINAL.blend` foi preservado como histórico e ainda contém os olhos ampliados e o dedo adicional rejeitados.

## O que mudou

- Recuperada a cabeça anterior à ampliação dos olhos, com os olhos alongados que você confirmou querer manter.
- Recuperadas as mãos com **três dedos e um polegar**, sem o dedo adicional.
- Arredondada a parte posterior do crânio. A frente da cabeça foi usada como alvo de preservação, sem redesenhar os olhos.
- Retopologia de todos os componentes, com malhas predominantemente em quads. Corpo e cabeça receberam novas malhas por fluxo de quadriláteros, seguidas de correção de simetria, emendas e inspeção. Olhos e orelhas aproveitaram a estrutura regular existente. O pescoço recebeu anéis próprios para dobrar.
- Maior resolução concentrada nas mãos, pés e orelhas, onde a primeira redução prejudicava os contornos. A malha de jogo tem aproximadamente **18,1 mil vértices de edição**, contra 114,4 mil no FBX de origem. Consulte os números exatos e triângulos exportados em `output/game_final_stats.json`.
- UVs novas e um mapa normal de rosto de 2048 × 2048, derivado da superfície original, incorporado ao Blender e ao GLB. A textura também está em `textures/chibi_head_normal.png`.

## Como animar no Blender

1. Selecione `RIG_Chibi` e entre em **Pose Mode**.
2. Use `root` para mover o personagem inteiro; `pelvis`, `spine`, `chest`, `neck` e `head` controlam o tronco e a cabeça.
3. Braços: `clavicle`, `upper_arm`, `forearm`, `hand`, com sufixos `.L` e `.R`.
4. Dedos: `index`, `middle` e `ring` têm três segmentos; `thumb` tem dois. Cada dedo pode ser ajustado separadamente.
5. Pernas: `thigh`, `shin`, `foot` e `toe`. Os ossos `eye.L/R` permitem movimentos limitados dos componentes dos olhos.

O esqueleto tem **46 ossos**, dos quais 45 são deformadores. É um rig **FK**: a rotação de cada osso move os filhos. Não inclui controles IK, sistema de pisada, retarget automático, rig facial de expressões ou sincronização labial. Os olhos originais são superfícies achatadas, portanto rotações grandes podem expor seus limites.

Há uma ação **`TEST_Deformacao_FK`**, com marcadores:

| Quadro | Teste |
|---:|---|
| 1 | T-pose / repouso |
| 20 | Braços abaixados |
| 40 | Cotovelos e joelho dobrados |
| 60 | Movimento da cabeça |
| 80 | Dedos fechados |

A ação serve para testar deformação; não é um ciclo de caminhada. Para começar uma animação própria, crie uma ação nova. Os modificadores de subdivisão opcionais ficam **desligados**, para mostrar a geometria efetivamente entregue ao jogo.

## Arquivos para importar no motor

- `output/character_GAME_RIGGED.glb`: malha, esqueleto, pesos e materiais com o mapa normal incorporado.
- `output/character_GAME_RIGGED.fbx`: malha e esqueleto em repouso; textura incorporada quando suportada pelo importador.
- `output/character_GAME_RIGGED.blend`: fonte editável, ação de teste e todos os checkpoints de referência acessíveis no projeto.

Os exports não incluem a ação de teste, câmeras, referências, fontes de alta resolução ou auxiliares de visualização. Cada vértice tem no máximo quatro influências normalizadas. Foi usada deformação linear, compatível com o fluxo comum de skinning de jogos. Configure o rig como esqueleto genérico no motor e adapte a associação de ossos se quiser retarget humanoide. A orientação no Blender é frente em −Y, Z para cima; os exportadores fazem a conversão para seus formatos.

## Revisão visual e técnica

Veja a pasta `renders/game/`:

- `runtime_three_quarter.png`, `runtime_face.png`, `runtime_hand.png`: aparência sem subdivisão.
- `topology_front.png`, `topology_face.png`, `topology_hand.png`: arestas reais da nova malha.
- `skeleton_front.png`: visualização do esqueleto dentro do personagem.
- `relaxed.png`, `joint_bend.png`, `hand_curl.png`: testes de deformação; alguns renders de diagnóstico usam a prévia subdividida.

Verificações em `output/validation_game_final_rest.json`: malhas fechadas individualmente, normais consistentes, ausência de faces degeneradas e vértices coincidentes dentro das tolerâncias do teste. As cinco poses de `output/game_pose_audit.json` não apresentaram autointerseções no corpo. O teste não garante todas as poses possíveis; ângulos extremos e poses com contato exigem revisão do animador.

Cabeça, pescoço, orelhas, olhos e pálpebras continuam componentes separados. Algumas junções se sobrepõem, como na origem. O mapa normal preserva aparência superficial, mas não acrescenta geometria ou deformadores faciais. As UVs são funcionais para esse bake, geradas automaticamente; podem ser reorganizadas numa etapa de texturização artística.

## Preservação e continuidade

- `SCULPT_SOURCE`: cópias de alta resolução do desenho recuperado, desativadas.
- `SOURCE_PARTS`: backups anteriores, desativados.
- `REFERENCES`: nove referências incorporadas, desativadas.
- `TOPOLOGY_REVIEW` e `RIG_REVIEW`: auxiliares de render, desativados e excluídos dos exports.
- `CHARACTER` e `RIG`: partes de trabalho.

Os novos marcos vão do **08 ao 13**, com revisões salvas. Continue pelo `.blend` novo indicado acima ou por `progress.json`. Não reaplique os scripts de transformação sobre o resultado: cada script declara seu checkpoint de entrada. O arquivo original `source/base.fbx` permanece intacto.
