Add-Type -AssemblyName System.Drawing
$canvas = New-Object System.Drawing.Bitmap 1800,1480
$graphics = [System.Drawing.Graphics]::FromImage($canvas)
$graphics.Clear([System.Drawing.Color]::FromArgb(240,242,242))
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$title = New-Object System.Drawing.Font 'Segoe UI',32,([System.Drawing.FontStyle]::Bold)
$label = New-Object System.Drawing.Font 'Segoe UI',15,([System.Drawing.FontStyle]::Bold)
$body = New-Object System.Drawing.Font 'Segoe UI',13
$dark = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(35,46,51))
$muted = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(90,102,107))
$pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(193,202,204)),1
$graphics.DrawString('TOPOLOGIA CORRIGIDA',$title,$dark,40,26)
$graphics.DrawString('Mãos, joelhos e virilha reconstruídos a partir das novas referências',$body,$muted,44,94)
$graphics.DrawLine($pen,40,141,1760,141)
function Draw-Panel([string]$file,[int]$col,[int]$row,[string]$caption,[string]$description) {
    $x=40+$col*590
    $y=170+$row*615
    $picture=[System.Drawing.Image]::FromFile((Join-Path $PSScriptRoot $file))
    $scale=[Math]::Min(540.0/$picture.Width,540.0/$picture.Height)
    $width=[int]($picture.Width*$scale)
    $height=[int]($picture.Height*$scale)
    $rect=New-Object System.Drawing.Rectangle ($x+[int]((540-$width)/2)),($y+[int]((540-$height)/2)),$width,$height
    $graphics.DrawImage($picture,$rect)
    $picture.Dispose()
    $graphics.DrawString($caption,$label,$dark,$x,($y+550))
    $graphics.DrawString($description,$body,$muted,$x,($y+579))
}
Draw-Panel 'hand_detail.png' 0 0 '01 / MÃO' 'Cinco dedos e loops nas articulações'
Draw-Panel 'knee_front.png' 1 0 '02 / PATELA' 'Contorno fechado em torno do joelho'
Draw-Panel 'hips_front.png' 2 0 '03 / VIRILHA' 'Raízes das pernas separadas'
Draw-Panel 'knee_side.png' 0 1 '04 / JOELHO LATERAL' 'Mais espaço na frente, menos atrás'
Draw-Panel 'knee_bent.png' 1 1 '05 / FLEXÃO DE 60°' 'Teste de geometria; shape key incluída'
Draw-Panel 'hips_under.png' 2 1 '06 / PONTE INFERIOR' 'Duas colunas de quads entre as pernas'
$graphics.DrawLine($pen,40,1420,1760,1420)
$graphics.DrawString('1.689 QUADS  /  3.378 TRIÂNGULOS',$label,$dark,40,1438)
$graphics.DrawString('Malha contínua  |  Simétrica  |  UVs  |  Blender / GLB / OBJ',$body,$muted,960,1441)
$canvas.Save((Join-Path $PSScriptRoot 'preview_topologia.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$canvas.Dispose()
$title.Dispose()
$label.Dispose()
$body.Dispose()
$dark.Dispose()
$muted.Dispose()
$pen.Dispose()
