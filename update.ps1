$zip = Get-ChildItem "$HOME\Downloads\critiq*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $zip) { Write-Host "No critiq zip found in Downloads"; exit }
$tmp = "$env:TEMP\critiq-update"
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive $zip.FullName -DestinationPath $tmp -Force
Copy-Item "$tmp\critiq\*" C:\Critiq\critiq -Recurse -Force
Write-Host "Updated from $($zip.Name)"
