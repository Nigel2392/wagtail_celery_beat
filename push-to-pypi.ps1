$ProjectName = "wagtail_celery_beat"

Function _PYPI_DistName {
    param (
        [string]$Version,
        [string]$Append = ".tar.gz"
    )

    return "$ProjectName-$Version$Append"
}

Function PYPI_Build {
    py .\setup.py sdist
}

Function PYPI_Check {
    param (
        [string]$Version
    )

    $distFile = _PYPI_DistName -Version $Version
    py -m twine check "./dist/${distFile}"
}

Function PYPI_Upload {
    param (
        [string]$Version
    )

    $distFile = _PYPI_DistName -Version $Version
    py -m twine upload "./dist/${distFile}"
}

function PYPI_NextVersion {
    param (
        [string]$ConfigFile = ".\setup.cfg",
        [string]$PyVersionFile = ".\${ProjectName}\__init__.py"
    )

    # Read file content
    $fileContent = Get-Content -Path $ConfigFile

    # Extract the version, increment it, and prepare the updated version string
    $versionLine = $fileContent | Where-Object { $_ -match "version\s*=" }
    $version = $versionLine -split "=", 2 | ForEach-Object { $_.Trim() } | Select-Object -Last 1
    $versionParts = $version -split "\."

    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]
    $patch = [int]$versionParts[2] + 1

    if ($patch -gt 9) {
        $patch = 0
        $minor += 1
    }

    if ($minor -gt 9) {
        $minor = 0
        $major += 1
    }

    $newVersion = "$major.$minor.$patch"
    Write-Host "Next version: $newVersion"

    # First update the init file so that in case something goes wrong 
    # the version doesn't persist in the config file
    $initContent = Get-Content -Path $PyVersionFile
    $initContent = $initContent -replace "__version__\s*=\s*.+", "__version__ = '$newVersion'"
    Set-Content -Path $PyVersionFile -Value $initContent

    # Update the version line in the file content
    $updatedContent = $fileContent -replace "version\s*=\s*.+", "version = $newVersion"

    # Write the updated content back to the file
    Set-Content -Path $ConfigFile -Value $updatedContent
    return $newVersion
}

$version = PYPI_NextVersion      # Increment the package version  (setup.cfg)
PYPI_Build                       # Build the package              (python setup.py sdist)
PYPI_Check -Version $version     # Check the package              (twine check dist/<LATEST>)
PYPI_Upload -Version $version    # Upload the package             (twine upload dist/<LATEST>)


