param ($path = $null, $src = ".\..\src\*.SemanticModel")

$currentFolder = (Split-Path $MyInvocation.MyCommand.Definition -Parent)

if ($path -eq $null) {
    $path =  $currentFolder
}

Set-Location $path

if ($src) {

    # Download Tabular Editor

    $destinationPath = "$currentFolder\_tools\TE"

    if (!(Test-Path "$destinationPath\TabularEditor.exe"))
    {
        New-Item -ItemType Directory -Path $destinationPath -ErrorAction SilentlyContinue | Out-Null            

        Write-Host "Downloading binaries"
    
        $downloadUrl = "https://github.com/TabularEditor/TabularEditor/releases/latest/download/TabularEditor.Portable.zip"
    
        $zipFile = "$destinationPath\TabularEditor.zip"
    
        Invoke-WebRequest -Uri $downloadUrl -OutFile $zipFile
    
        Expand-Archive -Path $zipFile -DestinationPath $destinationPath -Force     
    
        Remove-Item $zipFile          
    }    
    
    $rulesPath = "$currentFolder\bpa-semanticmodel-rules.json"

    if (!(Test-Path $rulesPath))
    {
        Write-Host "Downloading default BPA rules"
    
        Invoke-WebRequest -Uri "https://raw.githubusercontent.com/microsoft/Analysis-Services/master/BestPracticeRules/BPARules.json" -OutFile "$destinationPath\bpa-semanticmodel-rules.json"
        
        $rulesPath = "$destinationPath\bpa-semanticmodel-rules.json"
    }

    # Run BPA rules

    $itemsFolders = Get-ChildItem  -Path $src -recurse -include ("*.pbidataset", "*.pbism")

    foreach ($itemFolder in $itemsFolders) {
        $itemPath = "$($itemFolder.Directory.FullName)\definition"

        if (!(Test-Path $itemPath)) {
            $itemPath = "$($itemFolder.Directory.FullName)\model.bim"

            if (!(Test-Path $itemPath)) {
                throw "Cannot find semantic model definition."
            }
        }

        Write-Host "Running BPA rules for: '$itemPath'"

        $process = Start-Process -FilePath "$destinationPath\TabularEditor.exe" -ArgumentList """$itemPath"" -A ""$rulesPath"" -G" -NoNewWindow -Wait -PassThru    

        if ($process.ExitCode -ne 0) {
            throw "Error running BPA rules for: '$itemPath'"
        }    
    }
}
