$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$projectRoot = Split-Path -Parent $PSScriptRoot
$prefix = 'cartoon-female-chibi-character-base-mesh-3d-model-'
$font = New-Object System.Drawing.Font('Segoe UI', 17)
$smallFont = New-Object System.Drawing.Font('Segoe UI', 12)
$brush = [System.Drawing.Brushes]::WhiteSmoke

function Draw-Panel($graphics, $file, $x, $y, $label, $reference, $flip) {
    $im = [System.Drawing.Image]::FromFile($file)
    try {
        if ($flip) { $im.RotateFlip([System.Drawing.RotateFlipType]::RotateNoneFlipX) }
        $source = if ($reference) { [System.Drawing.RectangleF]::new(250,50,900,900) } else { [System.Drawing.RectangleF]::new(43,42,1308,1308) }
        $destination = [System.Drawing.RectangleF]::new($x,$y+38,600,600)
        $graphics.DrawImage($im,$destination,$source,[System.Drawing.GraphicsUnit]::Pixel)
        $graphics.DrawString($label,$font,$brush,[single]($x+18),[single]($y+7))
    } finally { $im.Dispose() }
}

function Make-Comparison($filename,$rows) {
    $canvas = [System.Drawing.Bitmap]::new(1200,($rows.Count*638+36))
    $graphics = [System.Drawing.Graphics]::FromImage($canvas)
    try {
        $graphics.Clear([System.Drawing.Color]::FromArgb(42,42,42))
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        for ($r=0; $r -lt $rows.Count; $r++) {
            $row=$rows[$r]
            Draw-Panel $graphics (Join-Path $projectRoot ('references/'+$prefix+$row.ref+'.jpg')) 0 ($r*638) ('REFERENCE / '+$row.label) $true $row.flip
            Draw-Panel $graphics (Join-Path $projectRoot ('renders/'+$row.render+'.png')) 600 ($r*638) ('MODEL / '+$row.label) $false $false
        }
        $graphics.DrawString('Equal character height. Side / three-quarter reference mirrored to match camera direction.',$smallFont,$brush,18,[single]($rows.Count*638+8))
        $canvas.Save((Join-Path $projectRoot ('renders/'+$filename)),[System.Drawing.Imaging.ImageFormat]::Png)
    } finally { $graphics.Dispose(); $canvas.Dispose() }
}

Make-Comparison 'comparison_front_side.png' @(
    @{ref='9a858a9e65';render='front';label='FRONT';flip=$false},
    @{ref='21b9f05615';render='side';label='SIDE';flip=$true}
)
Make-Comparison 'comparison_back_three_quarter.png' @(
    @{ref='b0b62758aa';render='back';label='BACK';flip=$false},
    @{ref='7e135165fc';render='three_quarter';label='THREE QUARTER';flip=$true}
)
$font.Dispose()
$smallFont.Dispose()
Write-Output 'Comparison sheets saved.'
