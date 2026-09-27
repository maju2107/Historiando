"""Build the OFL-licensed Historiando Mosaico display-font prototype.

Requires fonttools. The custom lowercase a is a smooth reconstruction of the
user's 31 x 35 reference, not an automatic pixel trace. Other base glyphs are
Palette Mosaic by Shibuya Font. Run from any directory.
"""
from pathlib import Path
import unicodedata
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen

ROOT = Path(__file__).parent
font = TTFont(ROOT / "PaletteMosaic-Regular.ttf")
pen = TTGlyphPen(None)
# Three separated mosaic pieces: small top bowl, large bottom bowl, right stem.
pen.moveTo((320, 600)); pen.qCurveTo((125, 610), (90, 450))
pen.lineTo((320, 450)); pen.closePath()
pen.moveTo((320, 365)); pen.qCurveTo((40, 365), (50, 150))
pen.qCurveTo((60, -10), (320, 0)); pen.closePath()
pen.moveTo((370, 600)); pen.lineTo((550, 600))
pen.lineTo((550, 0)); pen.lineTo((370, 0)); pen.closePath()
font['glyf']['a'] = pen.glyph()
font['hmtx']['a'] = (620, 50)
cmap = font.getBestCmap()
order = font.getGlyphOrder()
for char in 'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ':
    base, accent = unicodedata.normalize('NFD', char)
    name = 'uni%04X' % ord(char)
    base_name = cmap[ord(base)]
    glyph = font['glyf'][base_name]
    glyph.recalcBounds(font['glyf'])
    cx = (glyph.xMin + glyph.xMax) / 2
    y = glyph.yMax + 65
    marks = TTGlyphPen(font.getGlyphSet())
    glyph.draw(marks, font['glyf'])
    points = {
        '\u0301': [(cx-70,y),(cx+30,y+125),(cx+115,y+125),(cx+10,y)],
        '\u0300': [(cx+70,y),(cx-30,y+125),(cx-115,y+125),(cx-10,y)],
        '\u0302': [(cx-145,y),(cx-35,y+115),(cx+35,y+115),(cx+145,y),(cx+55,y),(cx,y+58),(cx-55,y)],
        '\u0303': [(cx-150,y),(cx-95,y+90),(cx-40,y+100),(cx+75,y+40),(cx+110,y+90),(cx+155,y+60),(cx+100,y-10),(cx+40,y-15),(cx-75,y+45),(cx-100,y-10)],
        '\u0327': [(cx-30,-25),(cx+40,-25),(cx+10,-90),(cx+65,-115),(cx+65,-175),(cx-45,-220),(cx-80,-175),(cx+5,-145),(cx-55,-120)],
    }
    if accent == '\u0308':
        for dx in [-110, 45]:
            marks.moveTo((cx+dx,y)); marks.lineTo((cx+dx+65,y)); marks.lineTo((cx+dx+65,y+80)); marks.lineTo((cx+dx,y+80)); marks.closePath()
    else:
        pts = points[accent]
        marks.moveTo(pts[0])
        for point in pts[1:]: marks.lineTo(point)
        marks.closePath()
    font['glyf'][name] = marks.glyph()
    font['hmtx'][name] = font['hmtx'][base_name]
    if 'vmtx' in font: font['vmtx'][name] = font['vmtx'][base_name]
    if name not in order: order.append(name)
    font.setGlyphOrder(order)
    for table in font['cmap'].tables:
        if table.isUnicode(): table.cmap[ord(char)] = name
names = {1:'Historiando Mosaico',2:'Regular',3:'HistoriandoMosaico-0.1',4:'Historiando Mosaico Regular',5:'Version 0.100',6:'HistoriandoMosaico-Regular',16:'Historiando Mosaico',17:'Regular'}
for record in font['name'].names:
    if record.nameID in names:
        record.string = names[record.nameID].encode(record.getEncoding())
font['OS/2'].sTypoAscender = 1100
font['OS/2'].usWinAscent = 1200
font['OS/2'].usWinDescent = 350
font.save(ROOT / 'HistoriandoMosaico-Regular.ttf')
print('Built HistoriandoMosaico-Regular.ttf with Portuguese diacritics.')
