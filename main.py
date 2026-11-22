import enum
import getpass
import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Button

def configurar_logging() -> logging.Logger:
    log_dir = Path.home() / ".config" / "festta"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"festta-log-{getpass.getuser()}.log"

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
                self.notify("Presença iniciada")
                self.mudar_estado(Estado.PRESENTE)

            case "btn_saida":
                self.notify("Saída registrada")
                self.mudar_estado(Estado.AUSENTE_TEMPORARIO)

            case "btn_retorno":
                self.notify("Retorno registrado")
                self.mudar_estado(Estado.PRESENTE)

            case "btn_fim":
                self.notify("Presença finalizada")
                self.exit()

    def aplicar_estado(self):

        btn_ini = self.query_one("#btn_ini", Button)
        btn_saida = self.query_one("#btn_saida", Button)
        btn_retorno = self.query_one("#btn_retorno", Button)
        btn_fim = self.query_one("#btn_fim", Button)

        # Esconde todos
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

        logger.info(
            "FSM: %s -> %s",
            self.estado.name,
            novo_estado.name
        )

        self.estado = novo_estado
        self.aplicar_estado()


if __name__ == "__main__":
    festtapp = Festta()
    logger.info("Aplicação iniciada.")
    festtapp.run()
