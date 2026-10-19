# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
[CmdletBinding()]
param(
    [switch]$CheckPublicReferences
)

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$qa = Join-Path $root 'build\copilot-app-demo-qa'
$manifestPath = Join-Path $qa 'deck-manifest.json'
$deckPath = Join-Path $root 'presentation\mosaic-copilot-app-demo-15min.pptx'
$pdfPath = Join-Path $root 'presentation\mosaic-copilot-app-demo-15min.pdf'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$findings = [System.Collections.Generic.List[object]]::new()
$slideChecks = [System.Collections.Generic.List[object]]::new()

function Assert-Deck {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) {
        throw $Message
    }
}

function Read-ZipXml {
    param($Archive, [string]$Name)
    $entry = $Archive.GetEntry($Name)
    Assert-Deck ($null -ne $entry) "Missing OOXML entry: $Name"
    $reader = [System.IO.StreamReader]::new($entry.Open())
    try {
        return [xml]$reader.ReadToEnd()
    }
    finally {
        $reader.Dispose()
    }
}

Assert-Deck ($manifest.mainSlides -eq 15) 'Expected 15 main slides.'
Assert-Deck ($manifest.totalSlides -eq 32) 'Expected the main story and complete 17-slide reference appendix.'
Assert-Deck ($manifest.allocatedSeconds -eq 900) 'The main story must total exactly 15 minutes.'
Assert-Deck ($manifest.features.Count -eq 60) 'Expected 60 feature-to-MOSAIC mappings.'
Assert-Deck ($manifest.builtInSkills.Count -eq 6) 'Expected all six documented built-in skills.'
Assert-Deck ($manifest.spokenWords -ge 1100 -and $manifest.spokenWords -le 1500) 'Narration must fit the 15-minute slot, including the recorded demo.'
Assert-Deck ([Math]::Abs($manifest.videoSeconds - 175.57) -lt 0.001) 'Keep the exact authentic recording duration.'

$archive = [System.IO.Compression.ZipFile]::OpenRead($deckPath)
try {
    $slideEntries = @($archive.Entries | Where-Object { $_.FullName -match '^ppt/slides/slide\d+\.xml$' })
    Assert-Deck ($slideEntries.Count -eq $manifest.totalSlides) 'PPTX slide count does not match the generated manifest.'
    $allNotes = [System.Collections.Generic.List[string]]::new()
    $slideText = @{}
    foreach ($entry in $manifest.slides) {
        $xml = Read-ZipXml $archive "ppt/slides/slide$($entry.number).xml"
        $slideText[[int]$entry.number] = ($xml.SelectNodes("//*[local-name()='t']") | ForEach-Object { $_.InnerText }) -join "`n"
        $hidden = $xml.DocumentElement.GetAttribute('show') -eq '0'
        Assert-Deck ($hidden -eq $entry.hidden) "Slide $($entry.number): incorrect hidden state."
        $notesXml = Read-ZipXml $archive "ppt/notesSlides/notesSlide$($entry.number).xml"
        $notes = ($notesXml.SelectNodes("//*[local-name()='t']") | ForEach-Object { $_.InnerText }) -join "`n"
        Assert-Deck ($notes.Contains($entry.talk)) "Slide $($entry.number): missing full speaker notes."
        foreach ($id in $entry.refs) {
            $url = $manifest.sources.$id[1]
            Assert-Deck ($notes.Contains($url)) "Slide $($entry.number): missing source $id."
        }
        if (-not $entry.hidden) {
            Assert-Deck ($notes.Contains('TIMING ')) "Slide $($entry.number): missing presenter timing."
        }
        $allNotes.Add($notes)
    }
    Assert-Deck ($manifest.slides[2].kind -eq 'positioning') 'Slide 3 must explicitly explain why to choose the App.'
    foreach ($phrase in @('IDE', 'GITHUB COPILOT APP', 'STANDALONE APPLICATION', 'Agent-directed work', 'not exclusive capabilities')) {
        Assert-Deck ($slideText[3].Contains($phrase)) "Slide 3 is missing required differentiation: $phrase"
    }
    foreach ($phrase in @('SHARED COPILOT CLI RUNTIME', 'MOSAIC PROCESS + VALIDATION WORKER', 'App models do not configure the separate worker')) {
        Assert-Deck ($slideText[8].Contains($phrase)) "Slide 8 is missing runtime attribution: $phrase"
    }
    foreach ($phrase in @('current IDE or execution tool', 'Effort, handoffs', 'No head-to-head result is claimed')) {
        Assert-Deck ($slideText[14].Contains($phrase)) "Slide 14 is missing comparative evaluation: $phrase"
    }
    Assert-Deck ($slideText[26].Contains('Claude Code')) 'The competitive appendix must address the named alternative.'
    Assert-Deck ($slideText[26].Contains('NEXT TO PROVE')) 'The competitive appendix must distinguish observed and proposed evidence.'
    $combinedNotes = $allNotes -join "`n"
    foreach ($feature in $manifest.features) {
        Assert-Deck ($combinedNotes.Contains("$($feature.id): $($feature.name)")) "Feature $($feature.id) missing from the actual deck."
        foreach ($command in $feature.commands) {
            Assert-Deck ($combinedNotes.Contains($command)) "Command $command missing from the actual deck."
        }
    }
    $mediaHashes = @(
        foreach ($entry in $archive.Entries) {
            if ($entry.FullName -notmatch '^ppt/media/[^/]+$') { continue }
            $stream = $entry.Open()
            try {
                [System.Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($stream)).ToLowerInvariant()
            }
            finally {
                $stream.Dispose()
            }
        }
    )
    Assert-Deck ($mediaHashes.Count -eq 3) 'Only the three approved authentic MOSAIC images may be embedded.'
    foreach ($evidence in $manifest.evidence) {
        Assert-Deck ($mediaHashes -contains $evidence.sha256) "Evidence image $($evidence.name) was changed or omitted."
    }
}
finally {
    $archive.Dispose()
}

$referenceCheck = [pscustomobject]@{ status = 'not-run'; reason = 'Use -CheckPublicReferences for current online reference coverage.' }
if ($CheckPublicReferences) {
    $base = 'https://docs.github.com/api/article/body?pathname='
    $commandBody = (Invoke-WebRequest -Uri ($base + '/en/copilot/reference/github-copilot-app-reference/slash-commands')).Content
    $skillBody = (Invoke-WebRequest -Uri ($base + '/en/copilot/reference/github-copilot-app-reference/built-in-skills')).Content
    $commandRows = @($commandBody -split "`n" | Where-Object { $_ -match '^\|\s*`/' })
    $documentedCommands = @(
        foreach ($row in $commandRows) {
            foreach ($match in [regex]::Matches(($row -split '\|')[1], '`([^`]+)`')) {
                ($match.Groups[1].Value -replace '\s+\[[^\]]+\]', '').Trim()
            }
        }
    )
    $documentedSkills = @(
        foreach ($row in ($skillBody -split "`n")) {
            if ($row -match '^\|\s*`([^`]+)`') { $Matches[1] }
        }
    )
    Assert-Deck ($commandRows.Count -eq 47) 'The public App command reference changed; refresh the deck coverage claim.'
    Assert-Deck ($documentedSkills.Count -eq 6) 'The built-in App skill reference changed; refresh the deck coverage claim.'
    foreach ($command in $documentedCommands) {
        Assert-Deck ($manifest.commands -contains $command) "Unmapped public App command: $command"
    }
    foreach ($skill in $documentedSkills) {
        Assert-Deck ($manifest.builtInSkills -contains $skill) "Unmapped built-in App skill: $skill"
    }
    $referenceCheck = [pscustomobject]@{
        status = 'pass'
        checkedAt = [DateTimeOffset]::UtcNow.ToString('o')
        publicCommandEntries = $commandRows.Count
        commandsIncludingAliases = $documentedCommands.Count
        builtInSkills = $documentedSkills
    }
}

$powerPoint = New-Object -ComObject PowerPoint.Application
$existingPresentations = $powerPoint.Presentations.Count
$presentation = $null
try {
    $presentation = $powerPoint.Presentations.Open($deckPath, -1, 0, 0)
    Assert-Deck ($presentation.Slides.Count -eq $manifest.totalSlides) 'Native PowerPoint could not load all slides.'
    $width = [double]$presentation.PageSetup.SlideWidth
    $height = [double]$presentation.PageSetup.SlideHeight
    Assert-Deck ([Math]::Abs($width / $height - 16 / 9) -lt 0.001) 'Expected a 16:9 presentation.'
    foreach ($slide in $presentation.Slides) {
        $textBoxes = [System.Collections.Generic.List[object]]::new()
        $pictures = [System.Collections.Generic.List[object]]::new()
        foreach ($shape in $slide.Shapes) {
            if ($shape.Left -lt -1 -or $shape.Top -lt -1 -or $shape.Left + $shape.Width -gt $width + 1 -or $shape.Top + $shape.Height -gt $height + 1) {
                $findings.Add([pscustomobject]@{ slide = $slide.SlideIndex; type = 'off-slide'; name = $shape.Name })
            }
            if ($shape.Type -in 11, 13) { $pictures.Add($shape) }
            if ($shape.HasTextFrame -ne -1 -or $shape.TextFrame2.HasText -ne -1) { continue }
            $range = $shape.TextFrame2.TextRange
            $textBox = [pscustomobject]@{
                text = $range.Text.Trim()
                left = [double]$range.BoundLeft
                top = [double]$range.BoundTop
                width = [double]$range.BoundWidth
                height = [double]$range.BoundHeight
                name = $shape.Name
            }
            $textBoxes.Add($textBox)
            if ($textBox.width -gt $shape.Width + 2 -or $textBox.height -gt $shape.Height + 2) {
                $findings.Add([pscustomobject]@{
                    slide = $slide.SlideIndex
                    type = 'text-overflow'
                    text = $textBox.text
                    actual = @($textBox.width, $textBox.height)
                    allowed = @([double]$shape.Width, [double]$shape.Height)
                })
            }
            if ($slide.SlideIndex -le 15 -and $shape.Name -eq 'content' -and $range.Font.Size -lt 20) {
                $findings.Add([pscustomobject]@{ slide = $slide.SlideIndex; type = 'small-body-text'; text = $textBox.text })
            }
        }
        for ($i = 0; $i -lt $textBoxes.Count; $i++) {
            $first = $textBoxes[$i]
            for ($j = $i + 1; $j -lt $textBoxes.Count; $j++) {
                $second = $textBoxes[$j]
                $overlapWidth = [Math]::Min($first.left + $first.width, $second.left + $second.width) - [Math]::Max($first.left, $second.left)
                $overlapHeight = [Math]::Min($first.top + $first.height, $second.top + $second.height) - [Math]::Max($first.top, $second.top)
                if ($overlapWidth -gt 2 -and $overlapHeight -gt 2) {
                    $findings.Add([pscustomobject]@{ slide = $slide.SlideIndex; type = 'text-text-overlap'; first = $first.text; second = $second.text })
                }
            }
            foreach ($picture in $pictures) {
                $overlapWidth = [Math]::Min($first.left + $first.width, $picture.Left + $picture.Width) - [Math]::Max($first.left, $picture.Left)
                $overlapHeight = [Math]::Min($first.top + $first.height, $picture.Top + $picture.Height) - [Math]::Max($first.top, $picture.Top)
                if ($overlapWidth -gt 2 -and $overlapHeight -gt 2) {
                    $findings.Add([pscustomobject]@{ slide = $slide.SlideIndex; type = 'text-image-overlap'; text = $first.text })
                }
            }
        }
        $slide.Export((Join-Path $qa ("slide-{0:D2}.png" -f $slide.SlideIndex)), 'PNG', 1920, 1080)
        $slideChecks.Add([pscustomobject]@{
            slide = $slide.SlideIndex
            hidden = $slide.SlideShowTransition.Hidden -eq -1
            textBoxes = $textBoxes.Count
            pictures = $pictures.Count
        })
    }
    # Export an all-slides view in memory; the source PPTX stays read-only.
    $hiddenStates = @($presentation.Slides | ForEach-Object { $_.SlideShowTransition.Hidden })
    try {
        foreach ($slide in $presentation.Slides) { $slide.SlideShowTransition.Hidden = 0 }
        $presentation.SaveAs($pdfPath, 32)
    }
    finally {
        for ($i = 1; $i -le $presentation.Slides.Count; $i++) {
            $presentation.Slides.Item($i).SlideShowTransition.Hidden = $hiddenStates[$i - 1]
        }
        $presentation.Saved = -1
    }
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        $null = [Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation)
    }
    if ($existingPresentations -eq 0) { $powerPoint.Quit() }
    $null = [Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint)
}

$report = [pscustomobject]@{
    status = $(if ($findings.Count -eq 0) { 'pass' } else { 'fail' })
    application = 'Microsoft PowerPoint'
    mainSlides = $manifest.mainSlides
    totalSlides = $slideChecks.Count
    durationSeconds = $manifest.allocatedSeconds
    featureMappings = $manifest.features.Count
    spokenWords = $manifest.spokenWords
    authenticImages = $manifest.evidence.Count
    publicReferenceCoverage = $referenceCheck
    slides = $slideChecks.ToArray()
    findings = $findings.ToArray()
    pdf = $pdfPath
}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $qa 'validation.json') -Encoding utf8
if ($findings.Count -gt 0) {
    $findings | ConvertTo-Json -Depth 6
    throw "Native PowerPoint found $($findings.Count) layout problem(s). See build\copilot-app-demo-qa\validation.json."
}
$report | Select-Object status, application, mainSlides, totalSlides, durationSeconds, featureMappings, spokenWords, authenticImages, publicReferenceCoverage, pdf | ConvertTo-Json -Depth 4
