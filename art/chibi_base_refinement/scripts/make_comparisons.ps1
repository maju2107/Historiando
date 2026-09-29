$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$projectRoot = Split-Path -Parent $PSScriptRoot
$prefix = 'cartoon-female-chibi-character-base-mesh-3d-model-'
$font = New-Object System.Drawing.Font('Segoe UI', 16)
$smallFont = New-Object System.Drawing.Font('Segoe UI', 11)
$brush = [System.Drawing.Brushes]::WhiteSmoke

function Draw-Panel($graphics, $file, $x, $y, $label, $reference, $flip) {
    $im = [System.Drawing.Image]::FromFile($file)
    try {
        if ($flip) { $im.RotateFlip([System.Drawing.RotateFlipType]::RotateNoneFlipX) }
        $scale = $im.Width / 1200.0
        $source = if ($reference) { [System.Drawing.RectangleF]::new(250,50,900,900) } else { [System.Drawing.RectangleF]::new((44*$scale),(41*$scale),(1112*$scale),(1112*$scale)) }
        $destination = [System.Drawing.RectangleF]::new($x,$y+38,600,600)
        $graphics.DrawImage($im,$destination,$source,[System.Drawing.GraphicsUnit]::Pixel)
        $graphics.DrawString($label,$font,$brush,[single]($x+18),[single]($y+7))
    } finally { $im.Dispose() }
}

function Make-Comparison($filename,$rows,$before) {
    $canvas = [System.Drawing.Bitmap]::new(1200,($rows.Count*638+36))
    $graphics = [System.Drawing.Graphics]::FromImage($canvas)
    try {
        $graphics.Clear([System.Drawing.Color]::FromArgb(42,42,42))
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        for ($r=0; $r -lt $rows.Count; $r++) {
            $row=$rows[$r]
            if ($before) {
                Draw-Panel $graphics (Join-Path $projectRoot ('renders/stage_00/'+$row.render+'.png')) 0 ($r*638) ('SEU FBX ORIGINAL / '+$row.label) $false $false
            } else {
                Draw-Panel $graphics (Join-Path $projectRoot ('references/'+$prefix+$row.ref+'.jpg')) 0 ($r*638) ('REFERENCIA / '+$row.label) $true $row.flip
            }
            Draw-Panel $graphics (Join-Path $projectRoot ('renders/'+$row.render+'.png')) 600 ($r*638) ('REFINADO / '+$row.label) $false $false
        }
        $caption = if ($before) { 'Mesma altura. Original com bloco auxiliar do quadril oculto; iluminacao diferente.' } else { 'Alturas alinhadas. Referencias lateral e 3/4 espelhadas; enquadramento 3/4 aproximado.' }
        $graphics.DrawString($caption,$smallFont,$brush,18,[single]($rows.Count*638+8))
        $canvas.Save((Join-Path $projectRoot ('renders/'+$filename)),[System.Drawing.Imaging.ImageFormat]::Png)
    } finally { $graphics.Dispose(); $canvas.Dispose() }
}
$frontSide=@(
    @{ref='9a858a9e65';render='front';label='FRENTE';flip=$false},
    @{ref='21b9f05615';render='side';label='LATERAL';flip=$true}
)
Make-Comparison 'comparison_front_side.png' $frontSide $false
Make-Comparison 'comparison_back_three_quarter.png' @(
    @{ref='b0b62758aa';render='back';label='COSTAS';flip=$false},
    @{ref='7e135165fc';render='three_quarter';label='3/4';flip=$true}
) $false
Make-Comparison 'before_after.png' $frontSide $true
$font.Dispose(); $smallFont.Dispose()
Write-Output 'Comparison sheets saved.'
