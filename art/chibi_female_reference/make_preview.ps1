Add-Type -AssemblyName System.Drawing
$canvas=New-Object System.Drawing.Bitmap 2000,1640
$g=[System.Drawing.Graphics]::FromImage($canvas)
$g.Clear([System.Drawing.Color]::FromArgb(34,39,37))
$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.TextRenderingHint=[System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$title=New-Object System.Drawing.Font 'Segoe UI',34,([System.Drawing.FontStyle]::Bold)
$label=New-Object System.Drawing.Font 'Segoe UI',15,([System.Drawing.FontStyle]::Bold)
$bodyFont=New-Object System.Drawing.Font 'Segoe UI',14
$white=New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(232,237,233))
$muted=New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(159,176,166))
$pen=New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(74,89,81)),1
$g.DrawString('CHIBI FEMININA / ESTUDO 3D',$title,$white,32,25)
$g.DrawString('Reconstrução no Blender a partir das nove vistas fornecidas',$bodyFont,$muted,37,98)
$g.DrawLine($pen,30,148,1970,148)
$panels=@(@('front.png','01 / FRENTE'),@('side.png','02 / PERFIL'),@('back.png','03 / COSTAS'),@('three_quarter.png','04 / TRÊS QUARTOS'),@('face_front.png','05 / ROSTO'),@('face_three_quarter.png','06 / DETALHE DO ROSTO'))
for($i=0;$i -lt 6;$i++) {
    $x=30+($i%3)*660
    $y=175+[int][Math]::Floor($i/3)*695
    $im=[System.Drawing.Image]::FromFile((Join-Path $PSScriptRoot $panels[$i][0]))
    $g.DrawImage($im,(New-Object System.Drawing.Rectangle $x,$y,620,620))
    $im.Dispose()
    $g.DrawString($panels[$i][1],$label,$white,$x,($y+634))
}
$g.DrawLine($pen,30,1565,1970,1565)
$g.DrawString('Malha editável  /  UVs  /  Subdivisão  /  Peças separadas',$bodyFont,$muted,33,1590)
$g.DrawString('BLENDER + GLB + OBJ',$label,$white,1630,1590)
$canvas.Save((Join-Path $PSScriptRoot 'preview.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $canvas.Dispose()

$canvas=New-Object System.Drawing.Bitmap 1900,1120
$g=[System.Drawing.Graphics]::FromImage($canvas)
$g.Clear([System.Drawing.Color]::FromArgb(34,39,37))
$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.TextRenderingHint=[System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.DrawString('REFERÊNCIA',$label,$white,30,44)
$g.DrawString('RECONSTRUÇÃO NO BLENDER',$label,$white,970,44)
$refPath='C:\Users\obran\OneDrive\Área de Trabalho\referencias\cartoon-female-chibi-character-base-mesh-3d-model-9a858a9e65.jpg'
$ref=[System.Drawing.Image]::FromFile($refPath)
$im=[System.Drawing.Image]::FromFile((Join-Path $PSScriptRoot 'front.png'))
$g.DrawImage($ref,(New-Object System.Drawing.Rectangle 30,105,900,900),250,50,900,900,[System.Drawing.GraphicsUnit]::Pixel)
$g.DrawImage($im,(New-Object System.Drawing.Rectangle 970,105,900,900),40,40,1320,1320,[System.Drawing.GraphicsUnit]::Pixel)
$ref.Dispose(); $im.Dispose()
$g.DrawString('Comparação de proporções e silhueta — imagens enquadradas em escala semelhante',$bodyFont,$muted,33,1060)
$canvas.Save((Join-Path $PSScriptRoot 'comparacao.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $canvas.Dispose()
$title.Dispose(); $label.Dispose(); $bodyFont.Dispose(); $white.Dispose(); $muted.Dispose(); $pen.Dispose()
