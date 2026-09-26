# K3 技能库安装器（Windows / 微软形态）
# 用法： powershell -ExecutionPolicy Bypass -File install.ps1 [-Target <技能位路径>]
param([string]$Target = "$env:USERPROFILE\.k3-skills")
Write-Host "== K3 Skill Library Installer (Windows) =="
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
New-Item -ItemType Directory -Force -Path $Target | Out-Null
Copy-Item -Recurse -Force "$here\skills\*" $Target
Write-Host "已复制技能至 $Target"
python "$here\verify_install.py" --target $Target --manifest "$here\MANIFEST.json"
if ($LASTEXITCODE -eq 0) { Write-Host "INSTALL PASS" } else { Write-Host "INSTALL FAIL — 见上方缺失清单"; exit 1 }
