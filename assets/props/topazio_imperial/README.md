# Topázio imperial coletável

`TopazioCollectible.tscn` é um `Area3D` sem colisão sólida. O cristal gira a 48°/s e oscila verticalmente em 10 cm. A esfera de coleta acompanha o centro do visual; ao entrar, o player recebe um fragmento pelo método existente `collect_gear()`, que também atualiza o HUD. A proteção `_collected` evita contagem repetida no mesmo frame.

O modelo semi-realista original tem 2.332 triângulos, uma malha, um material e três mapas PBR 2K embutidos. As instâncias compartilham o mesmo recurso. Os arquivos editáveis ficam em `art/topazio_imperial/semi_realista/`.

`_testes/cenario_ilha/TopaziosIlha.tscn` distribui 31 unidades: 25 formam um caminho desde a árvore do nascimento até o mirante, e seis continuam pelo parkour. O caminho contorna a árvore do santuário e inclui um degrau de acesso ao mirante. O cristal tem cerca de 63 cm de altura no jogo e fica com o centro 85 cm acima da superfície. Fases diferentes evitam flutuação sincronizada. As unidades coletadas permanecem removidas até reiniciar a cena.

Licença MIT, em `LICENSE.txt`; procedência e hashes em `asset_receipt.json`. A cópia veio do pacote verificado, preservando os bytes do GLB.
