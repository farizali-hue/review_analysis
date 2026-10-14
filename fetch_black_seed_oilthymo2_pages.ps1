$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$inputPath = "C:\Users\dell\OneDrive - Utopia\hassan\black_seed_oil_thymo\black_seed_oilthymo2_claims.xlsx"
$outDir = "D:\analysis\black_seed_oilthymo2_pages"
$csvPath = Join-Path $outDir "input_rows.csv"
$metaPath = Join-Path $outDir "fetch_metadata.json"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$python = "C:\Users\dell\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$extract = @"
import csv
import openpyxl

path = r"$inputPath"
out = r"$csvPath"
wb = openpyxl.load_workbook(path, data_only=True)
ws = wb.active
headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    for r in range(2, ws.max_row + 1):
        writer.writerow(dict(zip(headers, [ws.cell(r, c).value for c in range(1, ws.max_column + 1)])))
"@
$extract | & $python -

$headers = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    "Accept" = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    "Accept-Language" = "en-US,en;q=0.9"
    "Cache-Control" = "no-cache"
    "Pragma" = "no-cache"
}

$rows = Import-Csv -LiteralPath $csvPath
$results = @()

foreach ($row in $rows) {
    $asin = $row.asin
    $url = $row.url
    $filePath = Join-Path $outDir "$asin.html"
    $result = [ordered]@{
        asin = $asin
        url = $url
        file = $filePath
        status_code = $null
        length = 0
        fetched_at = (Get-Date).ToString("o")
        error = $null
    }

    try {
        $response = Invoke-WebRequest -Uri $url -Headers $headers -UseBasicParsing -TimeoutSec 45
        $content = $response.Content
        Set-Content -LiteralPath $filePath -Value $content -Encoding UTF8
        $result.status_code = [int]$response.StatusCode
        $result.length = $content.Length
    }
    catch {
        $result.error = $_.Exception.Message
    }

    $results += [pscustomobject]$result
    Start-Sleep -Milliseconds 750
}

$results | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $metaPath -Encoding UTF8
$results | Format-Table asin,status_code,length,error -AutoSize
