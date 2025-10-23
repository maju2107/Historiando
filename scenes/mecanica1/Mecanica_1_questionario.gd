extends Node2D

var grupo: ButtonGroup
var opcoes = ["Fogo", "Água", "Terra", "Ar"]

func _ready():
    # Cria um CanvasLayer para desenhar UI sobre o mundo 2D
    var ui_layer = CanvasLayer.new()
    add_child(ui_layer)

    # Cria um VBoxContainer (estrutura vertical de UI)
    var vbox = VBoxContainer.new()
    ui_layer.add_child(vbox)

    # Posiciona o container na tela (opcional)
    vbox.position = Vector2(100, 100)

    # Cria o grupo de botões
    grupo = ButtonGroup.new()

    # Cria botões dinamicamente
    for nome in opcoes:
        var botao = Button.new()
        botao.text = nome
        botao.toggle_mode = true
        botao.button_group = grupo
        botao.connect("pressed", Callable(self, "_ao_pressionar").bind(botao))
        vbox.add_child(botao)