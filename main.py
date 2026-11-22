from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Button

class Festta(App):

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

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="centro"):
            with Vertical():
                yield Button("Iniciar presença", id="btn_ini")
                yield Button("Registrar saída", id="btn_saida")
                yield Button("Registrar retorno", id="btn_retorno")
                yield Button("Finalizar presença", id="btn_fim")
                
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            case "btn_ini":
                self.notify("Iniciar presença")
            case "btn_saida":
                self.notify("Registrar saída")
            case "btn_retorno":
                self.notify("Registrar retorno")
            case "btn_fim":
                self.notify("Finalizar presença")

if __name__ == "__main__":
    festtapp = Festta()
    festtapp.run()
