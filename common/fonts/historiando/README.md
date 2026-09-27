# Historiando Mosaico — protótipo 0.1

Fonte TTF instalável e incorporada ao Godot. Derivada de **Palette Mosaic**,
dos autores do projeto Shibuya Font. Não é uma família inteiramente desenhada
do zero: mantém os glifos originais e altera o `a` minúsculo conforme a referência
do autor de Historiando. A reconstrução usa curvas vetoriais suaves; a referência
recebida tem apenas 31 × 35 pixels, portanto não representa um contorno de alta
resolução definitivo.

- Nome próprio: **Historiando Mosaico**, versão 0.100.
- `a`: três peças separadas, seguindo a imagem do usuário.
- Inclui acentos latinos para português, em maiúsculas e minúsculas, incluindo
  `á à â ã é ê í ó ô õ ú ü ç` e suas versões maiúsculas.
- Uso recomendado: títulos curtos e numeração grande. Para instruções, botões e
  textos longos, a interface usa Barlow Condensed.
- A marca da tela inicial continua sendo a arte original fornecida pelo usuário.
- Instalação opcional no Windows: abrir `HistoriandoMosaico-Regular.ttf` e escolher
  **Instalar**. Não é necessário instalar a fonte para executar o jogo.

## Reconstruir

```powershell
python -m pip install fonttools
python common/fonts/historiando/build_font.py
```

## Fontes e licenças

- Palette Mosaic: https://github.com/google/fonts/tree/main/ofl/palettemosaic
  e https://github.com/shibuyafont/Palette-mosaic-font-mono
- Barlow Condensed, de Jeremy Tribby:
  https://github.com/google/fonts/tree/main/ofl/barlowcondensed
- `OFL-PaletteMosaic.txt` cobre a original e a derivada Historiando Mosaico.
- `OFL-BarlowCondensed.txt` cobre Barlow Condensed.

Os avisos de copyright originais são preservados no TTF e nas licenças. A fonte
derivada, seu script de construção e sua documentação são distribuídos sob a
mesma SIL Open Font License 1.1. O redesenho do `a` parte da referência fornecida
pelo autor de Historiando. Não atribuir o desenho dos demais caracteres ao projeto.
