[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$deckPath = Join-Path $projectRoot 'presentation/mosaic-challenge-deck.pptx'
$pdfPath = Join-Path $projectRoot 'presentation/mosaic-challenge-deck.pdf'
$outputPath = Join-Path $projectRoot 'build/presentation-native'
$null = New-Item -ItemType Directory -Path $outputPath -Force
$powerPoint = New-Object -ComObject PowerPoint.Application
$existingPresentations = $powerPoint.Presentations.Count
$presentation = $null
$findings = [System.Collections.Generic.List[object]]::new()
$slideChecks = [System.Collections.Generic.List[object]]::new()

try {
    $presentation = $powerPoint.Presentations.Open($deckPath, -1, 0, 0)
    if ($presentation.Slides.Count -ne 3) {
        throw 'The submission must contain exactly three slides.'
    }
    foreach ($slide in $presentation.Slides) {
        $textBoxes = [System.Collections.Generic.List[object]]::new()
        $pictures = [System.Collections.Generic.List[object]]::new()
        foreach ($slideShape in $slide.Shapes) {
            if ($slideShape.Type -in 11, 13) {
                $pictures.Add($slideShape)
            }
            if ($slideShape.HasTextFrame -eq -1 -and $slideShape.TextFrame2.HasText -eq -1) {
                $textRange = $slideShape.TextFrame2.TextRange
                $textBox = [pscustomobject]@{
                    text = $textRange.Text.Trim()
                    left = [double]$textRange.BoundLeft
                    top = [double]$textRange.BoundTop
                    width = [double]$textRange.BoundWidth
                    height = [double]$textRange.BoundHeight
                }
                $textBoxes.Add($textBox)
                if ($textBox.width -gt $slideShape.Width + 2 -or $textBox.height -gt $slideShape.Height + 2) {
                    $findings.Add([pscustomobject]@{
                        slide = $slide.SlideIndex
                        type = 'text-overflow'
                        text = $textBox.text
                        textHeight = $textBox.height
                        boxHeight = [double]$slideShape.Height
                    })
                }
            }
        }
        foreach ($textBox in $textBoxes) {
            foreach ($picture in $pictures) {
                $overlapWidth = [Math]::Min($textBox.left + $textBox.width, $picture.Left + $picture.Width) - [Math]::Max($textBox.left, $picture.Left)
                $overlapHeight = [Math]::Min($textBox.top + $textBox.height, $picture.Top + $picture.Height) - [Math]::Max($textBox.top, $picture.Top)
                if ($overlapWidth -gt 2 -and $overlapHeight -gt 2) {
                    $findings.Add([pscustomobject]@{ slide = $slide.SlideIndex; type = 'text-image-overlap'; text = $textBox.text })
                }
            }
        }
        $slide.Export((Join-Path $outputPath "slide-$($slide.SlideIndex)-1280.png"), 'PNG', 1280, 720)
        $slide.Export((Join-Path $outputPath "slide-$($slide.SlideIndex)-3840.png"), 'PNG', 3840, 2160)
        $slideChecks.Add([pscustomobject]@{ slide = $slide.SlideIndex; textBoxes = $textBoxes.Count; pictures = $pictures.Count })
    }
    $presentation.SaveAs($pdfPath, 32)
    $report = [pscustomobject]@{
        status = $(if ($findings.Count -eq 0) { 'pass' } else { 'fail' })
        application = 'Microsoft PowerPoint'
        slides = $slideChecks.ToArray()
        findings = $findings.ToArray()
        pdf = $pdfPath
        imageSizes = @('1280x720', '3840x2160')
    }
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $outputPath 'validation.json') -Encoding utf8
    $report | ConvertTo-Json -Depth 6
    if ($findings.Count -gt 0) {
        throw "PowerPoint found $($findings.Count) layout problem(s)."
    }
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        $null = [Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation)
    }
    if ($existingPresentations -eq 0) {
        $powerPoint.Quit()
    }
    $null = [Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint)
}