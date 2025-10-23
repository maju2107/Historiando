extends Node2D

var grupo: ButtonGroup
var opcoes = ["A extinção da megafauna ocorreu devido a um grande meteoro que atingiu a Terra", "A extinção desses animais ocorreu devido ao aquecimento do clima e caça promovida pelos humanos ", "A extinção desses animais ocorreu devido a uma grande chuva toxica que os matou", "A extinção desses animais ocorreu devido a uma doença chamada Megafaunalite"]

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
    
    var label = $ColorRect/Label
    label.text = "O termo Megafauna é utilizado para se referir à diversidade de mamíferos gigantes que viveram no Pleistoceno (1,6 milhões de anos a 11.000 anos) e que atualmente encontram-se praticamente extintos. Sobre a extinção desses animais, escolha a alternativa correta:"