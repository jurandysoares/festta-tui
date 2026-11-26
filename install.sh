#!/usr/bin/env bash

set -euo pipefail

REPO="https://github.com/jurandysoares/festta-tui.git"
WORKDIR="${HOME}/Documents/festta-tui"

echo "========================================"
echo " Instalando e executando Festta TUI"
echo "========================================"

# 1. Instala o uv
echo "[1/5] Instalando astral-sh.uv..."

if ! command -v uv &>/dev/null; then
    winget install --id astral-sh.uv --exact \
        --accept-package-agreements \
        --accept-source-agreements
fi

# 2. Atualiza o PATH
echo "[2/5] Atualizando PATH..."

UV_PATH=$(where.exe uv.exe 2>/dev/null | head -n 1 | tr -d '\r' || true)

if [[ -n "$UV_PATH" ]]; then
    UV_DIR=$(cygpath -u "$(dirname "$UV_PATH")")
    export PATH="$UV_DIR:$PATH"
fi

if ! command -v uv &>/dev/null; then
    echo "ERRO: uv não encontrado no PATH."
    echo "Reinicie o Git Bash e execute novamente."
    exit 1
fi

uv --version

# 3. Cria o diretório Documents e clona o repositório
echo "[3/5] Clonando o repositório..."

mkdir -p "$(dirname "$WORKDIR")"

if [[ ! -d "$WORKDIR/.git" ]]; then
    git clone "$REPO" "$WORKDIR"
else
    echo "Repositório já existe."
fi

# 4. Entra no diretório
echo "[4/5] Entrando no diretório do projeto..."

cd "$WORKDIR"

# 5. Executa a aplicação
echo "[5/5] Executando Festta TUI..."

uv run main.py
