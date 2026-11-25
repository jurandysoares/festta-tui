import asyncio
import enum
import getpass
import json
import logging
import shutil
from pathlib import Path

import requests
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label

ENDPOINT_PRESENCA = "https://api.mange.ifrn.edu.br/presenca"
DIR_CONF = Path.home() / ".config" / "festta"
ARQUIVO_CONF = DIR_CONF / "festta-conf.json"


def configurar_logging() -> logging.Logger:
    DIR_CONF.mkdir(parents=True, exist_ok=True)
    log_file = DIR_CONF / f"festta-log-{getpass.getuser()}.log"

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        encoding="utf-8",
    )

    return logging.getLogger("festta")


logger = configurar_logging()


class Estado(enum.Enum):
    AGUARDANDO_INICIO = enum.auto()
    PRESENTE = enum.auto()
    AUSENTE_TEMPORARIO = enum.auto()
    ENCERRADO = enum.auto()


class MotivoSaidaScreen(ModalScreen[str]):

    CSS = """
    Screen {
        align: center middle;
    }

    Vertical {
        width: 60;
        height: auto;
        padding: 1;
        border: round $primary;
    }

    Input {
        margin: 1 0;
    }

    .botoes {
        width: 100%;
        align: center middle;
        height: auto;
    }
    
    .botoes Button {
        margin: 1 1;
        width: 20;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Informe o motivo da saída:")

            yield Input(
                placeholder="Ex.: Almoço, atendimento médico, reunião...",
                id="motivo"
            )

            with Horizontal(classes="botoes"):
                yield Button(
                    "Confirmar", 
                    id="confirmar", 
                    variant="success"
                )

                yield Button(
                    "Cancelar",
                    id="cancelar",
                    variant="default"
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirmar":
            motivo = self.query_one("#motivo", Input).value.strip()

            if motivo:
                self.dismiss(motivo)

        elif event.button.id == "cancelar":
            self.dismiss(None)


class Festta(App):

    estado: Estado = Estado.AGUARDANDO_INICIO
    TITLE = "Festta: Fast student attendance"
    SUB_TITLE = "Selecione uma opção"
    BINDINGS = [
        ("up", "focus_previous", "Anterior"),
        ("down", "focus_next", "Próximo")
    ]
    
    CSS = """
    #centro {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    Vertical {
        width: auto;
        align: center middle;
    }

    Button {
        width: 30;
        margin: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.estado: Estado = Estado.AGUARDANDO_INICIO

    def on_mount(self):
        self.aplicar_estado()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="centro"):
            with Vertical():
                yield Button("Iniciar presença", id="btn_ini", variant="success")
                yield Button("Registrar saída", id="btn_saida")
                yield Button("Registrar retorno", id="btn_retorno")
                yield Button("Finalizar presença", id="btn_fim", variant="error")
                
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            case "btn_ini":
                self.iniciar_presenca_worker()

            case "btn_saida":
                self.push_screen(
                    MotivoSaidaScreen(),
                    self.processar_saida
                )

            case "btn_retorno":
                self.notify("Retorno registrado")
                self.mudar_estado(Estado.PRESENTE)

            case "btn_fim":
                self.notify("Presença finalizada")
                self.exit()

    async def executar_script_conf(self) -> None:
        """Executa festta-conf.ps1 para gerar o arquivo ~/.config/festta/festta-conf.json."""
        script_ps1 = Path(__file__).resolve().parent / "festta-conf.ps1"

        if not script_ps1.exists():
            raise FileNotFoundError(f"Script não encontrado: {script_ps1}")

        executavel_ps = shutil.which("powershell") or shutil.which("pwsh")
        if not executavel_ps:
            raise RuntimeError("Executável do PowerShell não encontrado no PATH.")

        comando_ps = (
            "$ErrorActionPreference = 'Stop'; "
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            f"& '{script_ps1}'"
        )

        processo = await asyncio.create_subprocess_exec(
            executavel_ps,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            comando_ps,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await processo.communicate()
        if processo.returncode != 0:
            erro = stderr.decode("utf-8", errors="replace").strip()
            saida = stdout.decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"Falha ao executar festta-conf.ps1 (código {processo.returncode}): {erro or saida}"
            )

    async def obter_configuracao_presenca(self) -> dict:
        """Lê festta-conf.json se existir; caso contrário, gera via festta-conf.ps1 e lê."""
        if not ARQUIVO_CONF.exists():
            logger.info("Arquivo %s não encontrado. Executando festta-conf.ps1...", ARQUIVO_CONF)
            await self.executar_script_conf()

            if not ARQUIVO_CONF.exists():
                raise FileNotFoundError(
                    f"O script festta-conf.ps1 finalizou, mas {ARQUIVO_CONF} não foi criado."
                )
        else:
            logger.info("Carregando configuração existente de %s", ARQUIVO_CONF)

        # utf-8-sig ignora o BOM eventual gravado pelo Set-Content -Encoding UTF8 do Windows PowerShell
        conteudo = ARQUIVO_CONF.read_text(encoding="utf-8-sig")
        return json.loads(conteudo)

    @work(exclusive=True)
    async def iniciar_presenca_worker(self) -> None:
        btn_ini = self.query_one("#btn_ini", Button)
        btn_ini.disabled = True
        self.notify("Preparando dados e registrando presença...")

        try:
            payload = await self.obter_configuracao_presenca()
            logger.info("Enviando dados de presença: %s", payload)

            resposta = await asyncio.to_thread(
                requests.post,
                ENDPOINT_PRESENCA,
                json=payload,
                timeout=15,
            )
            resposta.raise_for_status()

            logger.info(
                "Presença iniciada com sucesso | status=%s | resposta=%s",
                resposta.status_code,
                resposta.text,
            )
            self.notify("Presença iniciada com sucesso!")
            self.mudar_estado(Estado.PRESENTE)

        except json.JSONDecodeError as exc:
            logger.exception("Conteúdo inválido em %s: %s", ARQUIVO_CONF, exc)
            self.notify("Erro: arquivo festta-conf.json inválido.", severity="error")

        except requests.RequestException as exc:
            logger.exception("Erro na requisição HTTP ao registrar presença: %s", exc)
            self.notify("Falha de comunicação com o servidor de presença.", severity="error")

        except Exception as exc:
            logger.exception("Erro ao iniciar presença: %s", exc)
            self.notify(f"Erro: {exc}", severity="error")

        finally:
            btn_ini.disabled = False

    def processar_saida(self, motivo: str | None) -> None:
        if motivo is None:
            logger.info("Solicitação de saída cancelada")
            self.notify("Operação cancelada")
            return
        
        logger.info("Saída registrada | motivo=%s", motivo)
        self.notify("Saída registrada")
        self.mudar_estado(Estado.AUSENTE_TEMPORARIO)

    def aplicar_estado(self):
        btn_ini = self.query_one("#btn_ini", Button)
        btn_saida = self.query_one("#btn_saida", Button)
        btn_retorno = self.query_one("#btn_retorno", Button)
        btn_fim = self.query_one("#btn_fim", Button)

        btn_ini.display = False
        btn_saida.display = False
        btn_retorno.display = False
        btn_fim.display = False

        match self.estado:
            case Estado.AGUARDANDO_INICIO:
                btn_ini.display = True

            case Estado.PRESENTE:
                btn_saida.display = True
                btn_fim.display = True

            case Estado.AUSENTE_TEMPORARIO:
                btn_retorno.display = True
                btn_fim.display = True

            case Estado.ENCERRADO:
                pass

    def mudar_estado(self, novo_estado: Estado):
        logger.info("FSM: %s -> %s", self.estado.name, novo_estado.name)
        self.estado = novo_estado
        self.aplicar_estado()


if __name__ == "__main__":
    festtapp = Festta()
    logger.info("Aplicação iniciada.")
    festtapp.run()