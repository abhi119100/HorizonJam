param(
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $root "_archive\releases"
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
[System.IO.Directory]::CreateDirectory($OutputDirectory) | Out-Null

$archiveName = "horizonjam-v3-baseline-2026-08-30.zip"
$archivePath = Join-Path $OutputDirectory $archiveName
$manifestPath = Join-Path $OutputDirectory "horizonjam-v3-baseline-2026-08-30.manifest.json"
$hashPath = "$archivePath.sha256"

$excludedDirectoryNames = @(
    ".git", ".next", "__pycache__", "node_modules"
)
$excludedPrefixes = @(
    "_archive\releases\",
    "RAG\unified_chroma_store\",
    "unified_chroma_store\",
    "audio\",
    "output\",
    "output_improved\"
)
$excludedExactPaths = @(
    ".env",
    ".env.production",
    "chord_analysis_output.json",
    "hello_moshi.wav",
    "results.json"
)
$excludedExtensions = @(
    ".h5", ".log", ".onnx", ".pb", ".pkl", ".pyc", ".pyo", ".tmp"
)

function Get-RelativePath([string]$FullName) {
    $resolved = [System.IO.Path]::GetFullPath($FullName)
    $rootPrefix = $root.TrimEnd("\") + "\"
    if (-not $resolved.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Archive input escaped repository root: $resolved"
    }
    return $resolved.Substring($rootPrefix.Length)
}

function Test-Included([System.IO.FileInfo]$File) {
    $relative = Get-RelativePath $File.FullName
    if ($excludedExactPaths -contains $relative) { return $false }
    if ($excludedExtensions -contains $File.Extension.ToLowerInvariant()) { return $false }
    foreach ($prefix in $excludedPrefixes) {
        if ($relative.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $false
        }
    }
    foreach ($part in $relative.Split([System.IO.Path]::DirectorySeparatorChar)) {
        if ($excludedDirectoryNames -contains $part) { return $false }
    }
    return $true
}

$files = Get-ChildItem -LiteralPath $root -File -Recurse -Force |
    Where-Object { Test-Included $_ } |
    Sort-Object FullName

$entries = foreach ($file in $files) {
    $relative = Get-RelativePath $file.FullName
    [ordered]@{
        path = $relative.Replace("\", "/")
        bytes = $file.Length
        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$totalBytes = ($files | Measure-Object -Property Length -Sum).Sum

$manifest = [ordered]@{
    schema_version = "horizonjam-source-archive-v1"
    release = "3.0.0-research-baseline"
    created_utc = [DateTime]::UtcNow.ToString("o")
    archive_name = $archiveName
    file_count = $files.Count
    total_uncompressed_bytes = $totalBytes
    exclusions = [ordered]@{
        directory_names = $excludedDirectoryNames
        prefixes = $excludedPrefixes
        exact_paths = $excludedExactPaths
        extensions = $excludedExtensions
        rationale = "Secrets, dependencies, caches, generated user output, unaudited stores, and model binaries are not distributable source."
    }
    files = $entries
}
$manifestJson = $manifest | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($manifestPath, $manifestJson, [System.Text.UTF8Encoding]::new($false))

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path -LiteralPath $archivePath) { Remove-Item -LiteralPath $archivePath -Force }
$zip = [System.IO.Compression.ZipFile]::Open($archivePath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($file in $files) {
        $relative = (Get-RelativePath $file.FullName).Replace("\", "/")
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $zip,
            $file.FullName,
            $relative,
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }
    $manifestEntry = $zip.CreateEntry("ARCHIVE_MANIFEST.json")
    $writer = [System.IO.StreamWriter]::new($manifestEntry.Open(), [System.Text.UTF8Encoding]::new($false))
    try { $writer.Write($manifestJson) } finally { $writer.Dispose() }
}
finally {
    $zip.Dispose()
}

$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText($hashPath, "$archiveHash  $archiveName`n", [System.Text.UTF8Encoding]::new($false))

[ordered]@{
    archive = $archivePath
    manifest = $manifestPath
    sha256_file = $hashPath
    sha256 = $archiveHash
    file_count = $files.Count
} | ConvertTo-Json
