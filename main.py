from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button

class Festta(App):

    CSS = """
    Screen {
        align: center middle;
    }

    Button {
        width: 20;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("Consultar")
        yield Footer()

    def on_button_pressed(self, event):
        self.notify("Botão clicado!")

if __name__ == "__main__":
    festtapp = Festta()
    festtapp.run()
