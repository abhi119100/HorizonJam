param(
    [string]$ArchivePath = "",
    [string]$ManifestPath = ""
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $ArchivePath) {
    $ArchivePath = Join-Path $root "_archive\releases\horizonjam-v3-baseline-2026-08-30.zip"
}
if (-not $ManifestPath) {
    $ManifestPath = Join-Path $root "_archive\releases\horizonjam-v3-baseline-2026-08-30.manifest.json"
}
$ArchivePath = (Resolve-Path -LiteralPath $ArchivePath).Path
$ManifestPath = (Resolve-Path -LiteralPath $ManifestPath).Path
$hashPath = "$ArchivePath.sha256"

$manifestText = [System.IO.File]::ReadAllText($ManifestPath)
$manifest = $manifestText | ConvertFrom-Json
$expectedArchiveHash = ([System.IO.File]::ReadAllText($hashPath).Trim() -split "\s+")[0]
$actualArchiveHash = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualArchiveHash -ne $expectedArchiveHash) {
    throw "Archive SHA-256 mismatch."
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)
try {
    $entries = @{}
    foreach ($entry in $zip.Entries) { $entries[$entry.FullName] = $entry }
    if ($entries.Count -ne ($manifest.file_count + 1)) {
        throw "Archive entry count does not match manifest."
    }
    if (-not $entries.ContainsKey("ARCHIVE_MANIFEST.json")) {
        throw "Embedded archive manifest is missing."
    }

    $reader = [System.IO.StreamReader]::new($entries["ARCHIVE_MANIFEST.json"].Open())
    try { $embeddedManifest = $reader.ReadToEnd() } finally { $reader.Dispose() }
    if ($embeddedManifest -ne $manifestText) {
        throw "Embedded and external manifests differ."
    }

    $forbidden = @(
        "(^|/)\.env$",
        "(^|/)\.env\.production$",
        "(^|/)node_modules/",
        "(^|/)\.next/",
        "(^|/)__pycache__/",
        "(^|/)unified_chroma_store/",
        "^audio/",
        "^output/",
        "^output_improved/"
    )

    foreach ($file in $manifest.files) {
        $path = [string]$file.path
        foreach ($pattern in $forbidden) {
            if ($path -match $pattern) { throw "Forbidden archive path: $path" }
        }
        if (-not $entries.ContainsKey($path)) { throw "Missing archive entry: $path" }
        $entry = $entries[$path]
        if ($entry.Length -ne [long]$file.bytes) { throw "Size mismatch: $path" }
        $stream = $entry.Open()
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try {
            $hash = $sha.ComputeHash($stream)
        }
        finally {
            $stream.Dispose()
            $sha.Dispose()
        }
        $actual = ([System.BitConverter]::ToString($hash)).Replace("-", "").ToLowerInvariant()
        if ($actual -ne [string]$file.sha256) { throw "File hash mismatch: $path" }
    }
}
finally {
    $zip.Dispose()
}

[ordered]@{
    archive = $ArchivePath
    archive_sha256 = $actualArchiveHash
    verified_files = $manifest.file_count
    forbidden_paths_found = 0
    result = "PASS"
} | ConvertTo-Json
