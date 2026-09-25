param(
    [int]$Port = 0,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StaticDir = Join-Path $AppDir 'static'
$DataDir = Join-Path $AppDir 'data'
$DataFile = Join-Path $DataDir 'issues.json'
$ConfigFile = Join-Path $AppDir 'config.json'

if (!(Test-Path $DataDir)) { New-Item -ItemType Directory -Path $DataDir | Out-Null }

# Normalize storage on startup. The original package shipped with a zero-byte
# issues.json, which exists but is not valid JSON and therefore skipped the
# old "create if missing" initialization.
$initializeDataFile = $false
if (!(Test-Path -LiteralPath $DataFile -PathType Leaf)) {
    $initializeDataFile = $true
} else {
    try {
        $existingRaw = Get-Content -LiteralPath $DataFile -Raw -Encoding UTF8
        if ([string]::IsNullOrWhiteSpace($existingRaw)) {
            $initializeDataFile = $true
        } else {
            $existingParsed = $existingRaw | ConvertFrom-Json
            if ($null -eq $existingParsed) { $initializeDataFile = $true }
        }
    } catch {
        $backup = "$DataFile.invalid.$([DateTime]::Now.ToString('yyyyMMdd-HHmmss')).bak"
        try { Copy-Item -LiteralPath $DataFile -Destination $backup -Force } catch { }
        $initializeDataFile = $true
    }
}
if ($initializeDataFile) {
    [IO.File]::WriteAllText($DataFile, "[]`r`n", [Text.UTF8Encoding]::new($false))
}

$config = Get-Content -LiteralPath $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Port -le 0) { $Port = [int]$config.port }

function Get-NowIso {
    return [DateTimeOffset]::Now.ToString('yyyy-MM-ddTHH:mm:sszzz')
}

function Get-Issues {
    try {
        $raw = Get-Content -LiteralPath $DataFile -Raw -Encoding UTF8
        if ([string]::IsNullOrWhiteSpace($raw)) { return @() }
        $items = $raw | ConvertFrom-Json
        if ($null -eq $items) { return @() }
        return @($items)
    } catch {
        Write-Warning "Could not read $DataFile. Starting with an empty list. Error: $($_.Exception.Message)"
        return @()
    }
}

function Save-Issues([object[]]$Issues) {
    $items = @($Issues)
    $tmp = "$DataFile.tmp"
    $bak = "$DataFile.bak"

    # -InputObject is important here: piping a one-item collection into
    # ConvertTo-Json lets PowerShell unwrap it. We always persist a JSON array.
    $json = ConvertTo-Json -InputObject $items -Depth 8

    if (Test-Path -LiteralPath $DataFile -PathType Leaf) {
        try { Copy-Item -LiteralPath $DataFile -Destination $bak -Force } catch { }
    }

    [IO.File]::WriteAllText($tmp, $json + "`r`n", [Text.UTF8Encoding]::new($false))

    # Verify the temp file before replacing live data.
    $verify = Get-Content -LiteralPath $tmp -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($null -eq $verify -and $items.Count -gt 0) { throw 'Temporary issue database verification failed.' }

    Move-Item -Force -LiteralPath $tmp -Destination $DataFile
}

function UrlDecode([string]$Value) {
    if ($null -eq $Value) { return '' }
    return [Uri]::UnescapeDataString(($Value -replace '\+', ' '))
}

function Parse-Query([string]$Query) {
    $result = @{}
    if ([string]::IsNullOrWhiteSpace($Query)) { return $result }
    foreach ($pair in $Query.TrimStart('?').Split('&')) {
        if (!$pair) { continue }
        $parts = $pair.Split('=', 2)
        $key = UrlDecode $parts[0]
        $value = if ($parts.Count -gt 1) { UrlDecode $parts[1] } else { '' }
        $result[$key] = $value
    }
    return $result
}

function Filter-Issues([object[]]$Issues, [hashtable]$Query) {
    $rows = @($Issues)
    if ($Query.ContainsKey('mode') -and $Query.mode) { $rows = @($rows | Where-Object { $_.mode -eq $Query.mode }) }
    if ($Query.ContainsKey('type') -and $Query.type) { $rows = @($rows | Where-Object { $_.issue_type -eq $Query.type }) }
    if ($Query.ContainsKey('area') -and $Query.area) { $rows = @($rows | Where-Object { $_.area -eq $Query.area }) }
    if ($Query.ContainsKey('priority') -and $Query.priority) { $rows = @($rows | Where-Object { $_.priority -eq $Query.priority }) }
    if ($Query.ContainsKey('status') -and $Query.status) { $rows = @($rows | Where-Object { $_.status -eq $Query.status }) }
    if ($Query.ContainsKey('quick')) {
        if ($Query.quick -eq 'open') {
            $rows = @($rows | Where-Object { $_.status -notin @('Complete', 'Deferred', "Won't Fix") })
        } elseif ($Query.quick -eq 'retest') {
            $rows = @($rows | Where-Object { $_.status -eq 'Retest' })
        }
    }
    if ($Query.ContainsKey('q') -and $Query.q) {
        $needle = $Query.q.ToLowerInvariant()
        $rows = @($rows | Where-Object {
            ("$($_.title)".ToLowerInvariant().Contains($needle)) -or
            ("$($_.notes)".ToLowerInvariant().Contains($needle)) -or
            ("$($_.mode)".ToLowerInvariant().Contains($needle))
        })
    }
    $p = @{ Critical = 1; High = 2; Normal = 3; Low = 4 }
    return @($rows | Sort-Object @{Expression={ if ($p.ContainsKey("$($_.priority)")) { $p["$($_.priority)"] } else { 9 } }}, @{Expression={$_.updated_at};Descending=$true}, @{Expression={[int]$_.id};Descending=$true})
}

function Get-LocalIPv4 {
    $addresses = @()
    try {
        $addresses = [System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() |
            Where-Object { $_.OperationalStatus -eq [System.Net.NetworkInformation.OperationalStatus]::Up } |
            ForEach-Object { $_.GetIPProperties().UnicastAddresses } |
            Where-Object {
                $_.Address.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and
                !$_.Address.IPAddressToString.StartsWith('127.') -and
                !$_.Address.IPAddressToString.StartsWith('169.254.')
            } |
            ForEach-Object { $_.Address.IPAddressToString } |
            Select-Object -Unique
    } catch { }
    return @($addresses)
}

function Escape-Csv([object]$Value) {
    $s = if ($null -eq $Value) { '' } else { "$Value" }
    return '"' + ($s -replace '"', '""') + '"'
}

function Make-Markdown([object[]]$Rows) {
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add('# ASM67 Current Test Issues')
    $lines.Add('')
    $lines.Add("Generated: $([DateTime]::Now.ToString('yyyy-MM-dd HH:mm'))")
    $lines.Add('')
    if ($Rows.Count -eq 0) { $lines.Add('No matching issues.'); return ($lines -join "`n") + "`n" }
    foreach ($status in @($config.statuses)) {
        $group = @($Rows | Where-Object { $_.status -eq $status })
        if ($group.Count -eq 0) { continue }
        $lines.Add("## $status"); $lines.Add('')
        foreach ($mode in @($group.mode | Select-Object -Unique)) {
            $lines.Add("### $mode"); $lines.Add('')
            foreach ($item in @($group | Where-Object { $_.mode -eq $mode })) {
                $lines.Add("- **#$($item.id)  -  $($item.issue_type) / $($item.area) / $($item.priority)**  -  $($item.title)")
                if ($item.notes) {
                    foreach ($ln in ("$($item.notes)" -split "`r?`n")) { if ($ln.Trim()) { $lines.Add("  - $ln") } }
                }
            }
            $lines.Add('')
        }
    }
    return ($lines -join "`n") + "`n"
}

function Make-ChatText([object[]]$Rows) {
    if ($Rows.Count -eq 0) { return 'No matching ASM67 issues.' }
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add('ASM67 testing issues to address:'); $lines.Add('')
    foreach ($mode in @($Rows.mode | Select-Object -Unique)) {
        $lines.Add("$mode")
        foreach ($item in @($Rows | Where-Object { $_.mode -eq $mode })) {
            $lines.Add("- #$($item.id) [$($item.issue_type) / $($item.area) / $($item.priority) / $($item.status)] $($item.title)")
            if ($item.notes) { $lines.Add("  Notes: $($item.notes)") }
        }
        $lines.Add('')
    }
    return ($lines -join "`n").TrimEnd() + "`n"
}

function Make-Csv([object[]]$Rows) {
    $fields = @('id','mode','issue_type','area','priority','title','notes','status','created_at','updated_at','completed_at')
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add(($fields | ForEach-Object { Escape-Csv $_ }) -join ',')
    foreach ($row in $Rows) {
        $lines.Add(($fields | ForEach-Object { Escape-Csv $row.$_ }) -join ',')
    }
    return ($lines -join "`r`n") + "`r`n"
}

function Mime-Type([string]$Path) {
    switch ([IO.Path]::GetExtension($Path).ToLowerInvariant()) {
        '.html' { 'text/html; charset=utf-8' }
        '.js'   { 'application/javascript; charset=utf-8' }
        '.css'  { 'text/css; charset=utf-8' }
        '.svg'  { 'image/svg+xml' }
        '.png'  { 'image/png' }
        '.ico'  { 'image/x-icon' }
        default { 'application/octet-stream' }
    }
}

function Send-Response($Stream, [int]$Status, [string]$ContentType, [byte[]]$Body, [string]$Disposition = '') {
    $reason = switch ($Status) { 200 {'OK'} 201 {'Created'} 204 {'No Content'} 400 {'Bad Request'} 404 {'Not Found'} 405 {'Method Not Allowed'} 500 {'Internal Server Error'} default {'OK'} }
    $headers = "HTTP/1.1 $Status $reason`r`nContent-Type: $ContentType`r`nContent-Length: $($Body.Length)`r`nCache-Control: no-store`r`nConnection: close`r`n"
    if ($Disposition) { $headers += "Content-Disposition: $Disposition`r`n" }
    $headers += "`r`n"
    $hb = [Text.Encoding]::ASCII.GetBytes($headers)
    $Stream.Write($hb,0,$hb.Length)
    if ($Body.Length -gt 0) { $Stream.Write($Body,0,$Body.Length) }
    $Stream.Flush()
}

function Send-Text($Stream, [int]$Status, [string]$Text, [string]$ContentType = 'text/plain; charset=utf-8', [string]$Disposition = '') {
    Send-Response $Stream $Status $ContentType ([Text.Encoding]::UTF8.GetBytes($Text)) $Disposition
}

function Send-Json($Stream, [int]$Status, $Object) {
    $json = ConvertTo-Json -InputObject $Object -Depth 10 -Compress
    Send-Text $Stream $Status $json 'application/json; charset=utf-8'
}

function Parse-Request($Client) {
    $stream = $Client.GetStream()
    $reader = New-Object IO.StreamReader($stream, [Text.Encoding]::UTF8, $false, 4096, $true)
    $requestLine = $reader.ReadLine()
    if (!$requestLine) { return $null }
    $parts = $requestLine.Split(' ')
    if ($parts.Count -lt 2) { return $null }
    $headers = @{}
    while ($true) {
        $line = $reader.ReadLine()
        if ($null -eq $line -or $line -eq '') { break }
        $idx = $line.IndexOf(':')
        if ($idx -gt 0) { $headers[$line.Substring(0,$idx).Trim().ToLowerInvariant()] = $line.Substring($idx+1).Trim() }
    }
    $body = ''
    if ($headers.ContainsKey('content-length')) {
        $length = [int]$headers['content-length']
        if ($length -gt 0) {
            $chars = New-Object char[] $length
            $read = 0
            while ($read -lt $length) {
                $n = $reader.Read($chars, $read, $length - $read)
                if ($n -le 0) { break }
                $read += $n
            }
            $body = -join $chars[0..([Math]::Max(0,$read-1))]
        }
    }
    return [pscustomobject]@{ Method=$parts[0].ToUpperInvariant(); Target=$parts[1]; Headers=$headers; Body=$body; Stream=$stream }
}

function Handle-Request($Req) {
    $stream = $Req.Stream
    $targetParts = $Req.Target.Split('?',2)
    $path = [Uri]::UnescapeDataString($targetParts[0])
    $query = Parse-Query $(if ($targetParts.Count -gt 1) { $targetParts[1] } else { '' })
    $issues = @(Get-Issues)

    try {
        if ($Req.Method -eq 'GET' -and $path -eq '/api/options') {
            return Send-Json $stream 200 @{ modes=@($config.modes); types=@($config.types); areas=@($config.areas); priorities=@($config.priorities); statuses=@($config.statuses) }
        }
        if ($Req.Method -eq 'GET' -and $path -eq '/api/serverinfo') {
            $ips = Get-LocalIPv4
            $urls = @($ips | ForEach-Object { "http://$($_):$Port/" })
            return Send-Json $stream 200 @{ port=$Port; ips=$ips; urls=$urls; primary_url=$(if($urls.Count){$urls[0]}else{"http://127.0.0.1:$Port/"}) }
        }
        if ($Req.Method -eq 'GET' -and $path -eq '/api/issues') {
            return Send-Json $stream 200 @(Filter-Issues $issues $query)
        }
        if ($Req.Method -eq 'GET' -and $path -eq '/api/copy') {
            return Send-Text $stream 200 (Make-ChatText @(Filter-Issues $issues $query))
        }
        if ($Req.Method -eq 'GET' -and $path -eq '/api/export/markdown') {
            return Send-Text $stream 200 (Make-Markdown @(Filter-Issues $issues $query)) 'text/markdown; charset=utf-8' 'attachment; filename="ASM67_CURRENT_TODO.md"'
        }
        if ($Req.Method -eq 'GET' -and $path -eq '/api/export/csv') {
            return Send-Text $stream 200 (Make-Csv @(Filter-Issues $issues $query)) 'text/csv; charset=utf-8' 'attachment; filename="ASM67_test_issues.csv"'
        }
        if ($Req.Method -eq 'POST' -and $path -eq '/api/issues') {
            $b = $Req.Body | ConvertFrom-Json
            foreach ($name in @('mode','issue_type','area','priority','title')) {
                if ([string]::IsNullOrWhiteSpace("$($b.$name)")) { return Send-Json $stream 400 @{error="missing required field: $name"} }
            }
            $next = if ($issues.Count) { ([int](($issues | Measure-Object -Property id -Maximum).Maximum)) + 1 } else { 1 }
            $now = Get-NowIso
            $obj = [pscustomobject]@{
                id=$next; mode="$($b.mode)"; issue_type="$($b.issue_type)"; area="$($b.area)"; priority="$($b.priority)";
                title="$($b.title)".Trim(); notes="$($b.notes)".Trim(); status=$(if($b.status){"$($b.status)"}else{'New'});
                created_at=$now; updated_at=$now; completed_at=$null
            }
            Save-Issues @($issues + $obj)
            return Send-Json $stream 201 $obj
        }
        if ($path -match '^/api/issues/(\d+)$') {
            $id = [int]$Matches[1]
            $found = @($issues | Where-Object { [int]$_.id -eq $id })
            if ($found.Count -eq 0) { return Send-Json $stream 404 @{error='not found'} }
            if ($Req.Method -eq 'PUT') {
                $b = $Req.Body | ConvertFrom-Json
                $item = $found[0]
                foreach ($field in @('mode','issue_type','area','priority','title','notes','status')) {
                    if ($null -ne $b.$field) { $item.$field = "$($b.$field)" }
                }
                $item.updated_at = Get-NowIso
                if ($item.status -eq 'Complete' -and !$item.completed_at) { $item.completed_at = Get-NowIso }
                if ($item.status -ne 'Complete') { $item.completed_at = $null }
                Save-Issues $issues
                return Send-Json $stream 200 $item
            }
            if ($Req.Method -eq 'DELETE') {
                Save-Issues @($issues | Where-Object { [int]$_.id -ne $id })
                return Send-Response $stream 204 'text/plain' ([byte[]]@())
            }
        }

        if ($Req.Method -ne 'GET') { return Send-Json $stream 405 @{error='method not allowed'} }
        $rel = if ($path -eq '/') { 'index.html' } else { $path.TrimStart('/') }
        if ($rel.Contains('..')) { return Send-Text $stream 404 'Not found' }
        $file = Join-Path $StaticDir $rel
        if (!(Test-Path -LiteralPath $file -PathType Leaf)) { return Send-Text $stream 404 'Not found' }
        $bytes = [IO.File]::ReadAllBytes($file)
        return Send-Response $stream 200 (Mime-Type $file) $bytes
    } catch {
        Write-Warning "Request failed: $($_.Exception.Message)"
        try { Send-Json $stream 500 @{error='server error'; detail=$_.Exception.Message} } catch { }
    }
}

$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $Port)
try {
    $listener.Start()
} catch {
    Write-Host ''
    Write-Host "Could not start the tracker on port $Port." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host 'Try closing another copy of the tracker, or edit config.json and choose another port.'
    exit 1
}

$ips = Get-LocalIPv4
$localUrl = "http://127.0.0.1:$Port/"
Write-Host ''
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ' ASM67 TEST ISSUE TRACKER' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host "Desktop: $localUrl" -ForegroundColor Green
if ($ips.Count) {
    Write-Host ''
    Write-Host 'Open one of these on your phone (same Wi-Fi):' -ForegroundColor Yellow
    foreach ($ip in $ips) { Write-Host "  http://$($ip):$Port/" -ForegroundColor Green }
} else {
    Write-Host 'No LAN IPv4 address was detected. Check Wi-Fi/network connection.' -ForegroundColor Yellow
}
Write-Host ''
Write-Host 'Data file:' $DataFile
Write-Host 'Press Ctrl+C in this window to stop the tracker.'
Write-Host 'If the phone cannot connect, run OPEN_FIREWALL.bat as Administrator once.' -ForegroundColor Yellow
Write-Host ''

if (!$NoBrowser) {
    try { Start-Process $localUrl } catch { }
}

try {
    while ($true) {
        $client = $listener.AcceptTcpClient()
        try {
            $req = Parse-Request $client
            if ($null -ne $req) { Handle-Request $req }
        } catch {
            Write-Warning $_.Exception.Message
        } finally {
            try { $client.Close() } catch { }
        }
    }
} finally {
    $listener.Stop()
}
