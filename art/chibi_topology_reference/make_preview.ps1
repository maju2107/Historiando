Add-Type -AssemblyName System.Drawing
$outputDir = $PSScriptRoot
$canvas = New-Object System.Drawing.Bitmap 1900,940
$graphics = [System.Drawing.Graphics]::FromImage($canvas)
$graphics.Clear([System.Drawing.Color]::FromArgb(240,242,242))
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$titleFont = New-Object System.Drawing.Font 'Segoe UI',34,([System.Drawing.FontStyle]::Bold)
$labelFont = New-Object System.Drawing.Font 'Segoe UI',15,([System.Drawing.FontStyle]::Bold)
$bodyFont = New-Object System.Drawing.Font 'Segoe UI',13
$smallFont = New-Object System.Drawing.Font 'Segoe UI',11
$darkBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(35,46,51))
$mutedBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(90,102,107))
$linePen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(193,202,204)),1
$graphics.DrawString('CHIBI / BASE MESH',$titleFont,$darkBrush,30,25)
$graphics.DrawString('Reconstructed in Blender from the supplied model sheet',$bodyFont,$mutedBrush,34,96)
$graphics.DrawLine($linePen,30,143,1870,143)
function Draw-Render([string]$name,[int]$x,[int]$y,[int]$width,[int]$height,[int]$cropX=0,[int]$cropWidth=0) {
    $render = [System.Drawing.Image]::FromFile((Join-Path $outputDir $name))
    if ($cropWidth -eq 0) { $cropWidth = $render.Width }
    $destination = New-Object System.Drawing.Rectangle $x,$y,$width,$height
    $graphics.DrawImage($render,$destination,$cropX,0,$cropWidth,$render.Height,[System.Drawing.GraphicsUnit]::Pixel)
    $render.Dispose()
}
Draw-Render 'front.png' 30 170 540 594
Draw-Render 'side.png' 590 170 340 594 185 630
Draw-Render 'back.png' 950 170 540 594
Draw-Render 'hand_detail.png' 1510 254 360 360
$graphics.DrawString('01 / FRONT',$labelFont,$darkBrush,30,785)
$graphics.DrawString('02 / SIDE',$labelFont,$darkBrush,590,785)
$graphics.DrawString('03 / BACK',$labelFont,$darkBrush,950,785)
$graphics.DrawString('04 / HAND DETAIL',$labelFont,$darkBrush,1510,640)
$graphics.DrawString('Thumb + two finger groups',$smallFont,$mutedBrush,1510,676)
$graphics.DrawLine($linePen,30,852,1870,852)
$graphics.DrawString('805 QUADS  /  1,610 TRIANGLES',$labelFont,$darkBrush,30,879)
$graphics.DrawString('Continuous mesh   |   UV unwrapped   |   Unrigged   |   .blend / .glb / .obj',$bodyFont,$mutedBrush,770,883)
$canvas.Save((Join-Path $outputDir 'preview.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$canvas.Dispose()
$titleFont.Dispose()
$labelFont.Dispose()
$bodyFont.Dispose()
$smallFont.Dispose()
$darkBrush.Dispose()
$mutedBrush.Dispose()
$linePen.Dispose()
