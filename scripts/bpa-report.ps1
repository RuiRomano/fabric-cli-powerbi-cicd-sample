param ($path = $null, $src = ".\..\src\*.Report")

$currentFolder = (Split-Path $MyInvocation.MyCommand.Definition -Parent)

if ($path -eq $null) {
    $path =  $currentFolder
}

Set-Location $path

if ($src) {

    # Download Tabular Editor

    $destinationPath = "$currentFolder\_tools\PBIInspector"

    if (!(Test-Path "$destinationPath\win-x64\CLI\PBIRInspectorCLI.exe"))
    {
        New-Item -ItemType Directory -Path $destinationPath -ErrorAction SilentlyContinue | Out-Null            

        Write-Host "Downloading binaries"
    
        $downloadUrl = "https://github.com/NatVanG/PBI-InspectorV2/releases/download/v2.2.0/win-x64-CLI.zip"
    
        $zipFile = "$destinationPath\PBIInspector.zip"
    
        Invoke-WebRequest -Uri $downloadUrl -OutFile $zipFile
    
        Expand-Archive -Path $zipFile -DestinationPath $destinationPath -Force     
    
        Remove-Item $zipFile          
    }    
    
    $rulesPath = "$currentFolder\bpa-report-rules.json"

    if (!(Test-Path $rulesPath))
    {
        Write-Host "Downloading default BPA rules"
    
        Invoke-WebRequest -Uri "https://raw.githubusercontent.com/NatVanG/PBI-InspectorV2/refs/heads/main/Rules/Base-rules.json" -OutFile "$destinationPath\bpa-report-rules.json"
        
        $rulesPath = "$destinationPath\bpa-report-rules.json"
    }

    # Run BPA rules

    $itemsFolders = Get-ChildItem  -Path $src -recurse -include ("*.pbir")

    foreach ($itemFolder in $itemsFolders) {	
        $itemPath = "$($itemFolder.Directory.FullName)\definition"

        if (!(Test-Path $itemPath)) {
              if (!(Test-Path $itemPath)) {
                throw "Cannot find report PBIR definition. If you are using PBIR-Legacy (report.json), please convert it to PBIR using Power BI Desktop."
            }
        }

        Write-Host "Running BPA rules for: '$itemPath'"

        $process = Start-Process -FilePath "$destinationPath\win-x64\CLI\PBIRInspectorCLI.exe" -ArgumentList "-pbipreport ""$itemPath"" -rules ""$rulesPath"" -formats ""GitHub""" -NoNewWindow -Wait -PassThru    

        if ($process.ExitCode -ne 0) {
            throw "Error running BPA rules for: '$itemPath'"
        }    
    }
}