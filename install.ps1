$ErrorActionPreference = "Stop"

# Configurações
$REPO = "https://github.com/jurandysoares/festta-tui.git"
$WORKDIR = Join-Path $HOME "Documents\festta-tui"

Write-Host "========================================"
Write-Host " Instalando e executando Festta TUI"
Write-Host "========================================"

# 1. Instala o uv
Write-Host "`n[1/5] Instalando astral-sh.uv..."

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    winget install --id astral-sh.uv --exact `
        --accept-package-agreements `
        --accept-source-agreements

    if ($LASTEXITCODE -ne 0) {
        throw "Falha na instalação do uv."
    }
}
else {
    Write-Host "uv já está instalado."
}

# 2. Atualiza o PATH da sessão atual
Write-Host "`n[2/5] Atualizando PATH..."

$env:Path = [System.Environment]::GetEnvironmentVariable(
    "Path", "Machine"
) + ";" + [System.Environment]::GetEnvironmentVariable(
    "Path", "User"
) + ";" + $env:Path

# Verifica o uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv não encontrado no PATH. Reinicie o PowerShell e tente novamente."
}

uv --version

# 3. Clona o repositório
Write-Host "`n[3/5] Clonando o repositório..."

$PARENT = Split-Path $WORKDIR -Parent

New-Item -ItemType Directory -Force -Path $PARENT | Out-Null

if (-not (Test-Path (Join-Path $WORKDIR ".git"))) {
    git clone $REPO $WORKDIR

    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao clonar o repositório."
    }
}
else {
    Write-Host "Repositório já existe."
}

# 4. Entra no diretório
Write-Host "`n[4/5] Entrando no diretório do projeto..."

Set-Location $WORKDIR

# 5. Executa a aplicação
Write-Host "`n[5/5] Executando Festta TUI..."

uv run main.py

if ($LASTEXITCODE -ne 0) {
    throw "Falha na execução do Festta TUI."
}
