$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$outDir = "D:\analysis\black_seed_thymo2_pages"
$metaPath = Join-Path $outDir "fetch_metadata.json"

New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$headers = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    "Accept" = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    "Accept-Language" = "en-US,en;q=0.9"
    "Cache-Control" = "no-cache"
    "Pragma" = "no-cache"
}

$products = @(
    @{ asin = "B0DQ3774GD"; url = "https://www.amazon.com/dp/B0DQ3774GD" },
    @{ asin = "B0GHM7VV81"; url = "https://www.amazon.com/dp/B0GHM7VV81" },
    @{ asin = "B0GFP46CNQ"; url = "https://www.amazon.com/dp/B0GFP46CNQ" },
    @{ asin = "B0938R37X3"; url = "https://www.amazon.com/dp/B0938R37X3" },
    @{ asin = "B0CLB3FZ5M"; url = "https://www.amazon.com/dp/B0CLB3FZ5M" },
    @{ asin = "B08NYHVHZ6"; url = "https://www.amazon.com/dp/B08NYHVHZ6" }
)

$results = @()

foreach ($product in $products) {
    $asin = $product.asin
    $url = $product.url
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
