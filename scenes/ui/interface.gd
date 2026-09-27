extends Control
## Shared screen system. Existing entry points instantiate this scene without
## changing gameplay/save paths. Coordinates use a centered 1600 x 900 canvas.
signal close_requested
signal restart_requested
const Kit = preload("res://scenes/ui/ui_kit.gd")
const Backdrop = preload("res://scenes/ui/comic_backdrop.gd")
const Hud = preload("res://scenes/ui/historiando_hud.gd")
const ComicPanel = preload("res://scenes/ui/comic_panel.gd")
const Credits = preload("res://scenes/ui/credit_data.gd")
const ISLAND_PATH := "res://_testes/cenario_ilha/CenarioIlha.tscn"
const SETTINGS_PATH := "user://interface.cfg"
@export_enum("home", "chapters", "pause", "demo", "retry") var initial_screen := "home"
var screen := ""
var canvas: Control
var content: Control
var first_button: Button
var demo_hud: Control
var back_screen := "home"
var loading := false
var modal: Control
var modal_action: Callable
var modal_focus: Control
var suspended_controls: Array[Dictionary] = []

func _input(event: InputEvent) -> void:
	if is_instance_valid(modal) and (event.is_action_pressed("ui_cancel") or event.is_action_pressed("menu")):
		dismiss_modal()
		get_viewport().set_input_as_handled()

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group("historiando_menu")
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	canvas = Control.new()
	canvas.size = Vector2(1600,900)
	add_child(canvas)
	get_viewport().size_changed.connect(_resize)
	_resize()
	show_screen(initial_screen)

func _resize() -> void:
	var viewport := get_viewport_rect().size
	var factor := minf(viewport.x/1600.0,viewport.y/900.0)
	canvas.scale = Vector2.ONE*factor
	canvas.position = (viewport-Vector2(1600,900)*factor)/2

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if screen == "retry": return
		elif screen == "pause": close_requested.emit()
		elif screen == "settings" or screen == "about": show_screen(back_screen)
		elif screen == "type": show_screen("about")
		elif screen != "home": show_screen("home")
		get_viewport().set_input_as_handled()

func show_screen(next: String) -> void:
	if is_instance_valid(modal): dismiss_modal()
	if content:
		canvas.remove_child(content)
		content.queue_free()
	if is_instance_valid(demo_hud):
		demo_hud.queue_free()
		demo_hud = null
	screen = next
	content = Control.new()
	content.size = Vector2(1600,900)
	canvas.add_child(content)
	first_button = null
	var bg := Backdrop.new()
	bg.size = Vector2(1600,900)
	bg.landscape = next in ["home", "demo"]
	content.add_child(bg)
	match next:
		"home": _home()
		"chapters": _chapters()
		"settings": _settings()
		"about": _about()
		"pause": _pause_menu()
		"demo": _demo()
		"retry": _retry_menu()
		"type": _font_specimen()
		"credits": _credits()
	if first_button: first_button.grab_focus()
	if not bool(load_settings().get_value("accessibility","reduce_motion",false)):
		content.modulate.a = 0.0
		create_tween().tween_property(content,"modulate:a",1.0,0.18)

func _footer(words: String = "↑ ↓  NAVEGAR       ENTER  SELECIONAR       ESC  VOLTAR") -> void:
	Kit.rect(content,Rect2(55,852,1490,1),Color("68516c"))
	Kit.label(content,words,Rect2(60,863,1180,27),19,Kit.PAPER)
	Kit.texture(content,"res://assets/ui/historiando/brand_wordmark.svg",Rect2(1305,856,235,39))

func _header(kicker: String, title: String) -> void:
	Kit.brand(content,Rect2(60,39,55,55),true)
	Kit.label(content,kicker,Rect2(135,49,1200,36),23,Kit.GOLD,Kit.BOLD)
	Kit.label(content,title,Rect2(65,122,1350,92),66,Kit.PAPER,Kit.BOLD)

func _home() -> void:
	Kit.brand(content,Rect2(61,46,58,58),true)
	Kit.label(content,"CADA HISTÓRIA, UMA NOVA DESCOBERTA.",Rect2(137,57,485,35),22,Kit.GOLD,Kit.BOLD)
	Kit.brand(content,Rect2(64,178,505,139))
	Kit.label(content,"O passado está vivo.\nExplore.",Rect2(72,342,520,145),59,Kit.PAPER,Kit.BOLD)
	Kit.label(content,"Atravesse o tempo. Encontre novas histórias.",Rect2(75,498,515,40),25,Kit.PAPER)
	first_button = Kit.button(content,"COMEÇAR A JORNADA    ›",Rect2(74,566,470,86),func(): show_screen("chapters"))
	Kit.button(content,"AJUSTES",Rect2(74,672,224,59),func(): _open_settings("home"),Kit.PAPER,true)
	Kit.button(content,"SOBRE O JOGO",Rect2(313,672,230,59),func(): _open_about("home"),Kit.PAPER,true)
	Kit.button(content,"CRÉDITOS",Rect2(74,751,320,53),func(): show_screen("credits"),Kit.CLAY,true)
	Kit.button(content,"SAIR",Rect2(411,751,133,53),_confirm_exit,Kit.PAPER,true)
	Kit.rect(content,Rect2(706,102,279,39),Kit.INK)
	Kit.label(content,"UMA AVENTURA PELO TEMPO",Rect2(719,105,265,34),20,Kit.PAPER,Kit.BOLD)
	Kit.rect(content,Rect2(1208,700,258,63),Kit.INK)
	Kit.label(content,"EXPLORE. DESCUBRA. VIVA.",Rect2(1224,707,245,43),23,Kit.GOLD,Kit.BOLD)
	_footer("TECLADO OU CONTROLE  /  SUA JORNADA COMEÇA AQUI")

func _chapters() -> void:
	_header("SUA JORNADA", "Escolha seu próximo capítulo.")
	Kit.label(content,"Cada descoberta abre um novo caminho.",Rect2(69,220,1050,40),28)
	var progress := get_node_or_null("/root/FaseCore")
	var unlocked := [true, bool(progress and progress.fase1_concluida), bool(progress and progress.fase2_concluida)]
	var completed := [bool(progress and progress.fase1_concluida),bool(progress and progress.fase2_concluida),bool(progress and progress.fase3_concluida)]
	var names := ["A ilha de Pindorama", "Novos caminhos", "Além do horizonte"]
	var colors := [Kit.GOLD,Kit.CLAY,Kit.GREEN]
	for i in range(3):
		var x := 72.0+float(i)*496.0
		Kit.rect(content,Rect2(x+7,307,466,414),Color("0e0018"))
		Kit.rect(content,Rect2(x,299,464,414),colors[i] if unlocked[i] else Color("34213f"))
		Kit.label(content,"CAPÍTULO",Rect2(x+27,321,370,34),23,Kit.INK if unlocked[i] else Kit.PAPER,Kit.BOLD)
		Kit.label(content,"0%d" % (i+1),Rect2(x+24,350,400,158),136,Kit.INK if unlocked[i] else Color("796781"),Kit.DISPLAY)
		Kit.label(content,names[i],Rect2(x+27,529,410,61),39,Kit.INK if unlocked[i] else Kit.PAPER,Kit.BOLD)
		var hint: String = "PROTÓTIPO 3D  /  EXPLORE A ILHA" if i == 0 else ("CONCLUÍDO  /  JOGAR NOVAMENTE" if completed[i] else ("PRONTO PARA EXPLORAR" if unlocked[i] else "CONCLUA O CAPÍTULO %02d" % i))
		Kit.label(content,hint,Rect2(x+28,596,410,33),21,Kit.INK if unlocked[i] else Kit.PAPER,Kit.BOLD)
		var play := Kit.button(content,"EXPLORAR   ›" if unlocked[i] else "BLOQUEADO",Rect2(x+24,642,414,57),_launch_chapter.bind(i+1),Kit.PAPER,true)
		play.disabled = not unlocked[i]
		if i == 0: first_button = play
	Kit.button(content,"‹   VOLTAR",Rect2(72,756,220,59),func(): show_screen("home"),Kit.PAPER,true)
	_footer()

func _open_settings(previous: String) -> void:
	back_screen = previous
	show_screen("settings")

func _open_about(previous: String) -> void:
	back_screen = previous
	show_screen("about")

func _credits() -> void:
	_header("QUEM FAZ ESSA HISTÓRIA", "Créditos & fontes dos assets")
	Kit.label(content,"Arte, natureza, música e letras que dão vida a Pindorama.",Rect2(70,216,1390,43),28)
	var panel := ComicPanel.new()
	panel.position = Vector2(72,278)
	panel.size = Vector2(1456,436)
	panel.fill = Color("2b1539")
	panel.textured = false
	content.add_child(panel)
	var text := RichTextLabel.new()
	text.name = "AssetCredits"
	text.position = Vector2(106,300)
	text.size = Vector2(1380,387)
	text.bbcode_enabled = true
	text.scroll_active = true
	text.focus_mode = Control.FOCUS_ALL
	text.add_theme_font_override("normal_font",Kit.BODY)
	text.add_theme_font_override("bold_font",Kit.BOLD)
	text.add_theme_font_size_override("normal_font_size",27)
	text.add_theme_font_size_override("bold_font_size",29)
	text.add_theme_color_override("default_color",Kit.PAPER)
	text.add_theme_constant_override("line_separation",5)
	text.meta_clicked.connect(func(url: Variant):
		if str(url).begins_with("https://"): OS.shell_open(str(url)))
	var words := "[color=#dda63b][b]HISTORIANDO / PINDORAMA[/b][/color]\nIdentidade visual e marcas: artes originais do projeto Historiando.\n\n[color=#dda63b][b]ASSETS DOS CENÁRIOS[/b][/color]\n"
	for entry: Dictionary in Credits.ENTRIES:
		var author: String = entry.author
		if author == "Creative Trio": author = "Creative Trio (CreativeTrio)"
		words += "\n[b]%02d  /  %s[/b]\n%s · %s\n%s\n" % [entry.id,entry.title,author,entry.source,entry.license]
		words += "[color=#dda63b][url=%s]PÁGINA DO ASSET ↗[/url][/color]    " % entry.url
		var regex := RegEx.new()
		regex.compile("https://[^\\s]+")
		var sources := regex.search_all(entry.license_source)
		for index in range(sources.size()):
			words += "[color=#dda63b][url=%s]FONTE DA LICENÇA%s ↗[/url][/color]    " % [sources[index].get_string()," %d" % (index+1) if sources.size()>1 else ""]
		words += "\n"
	words += "\n[color=#dda63b][b]TIPOGRAFIA[/b][/color]\nHistoriando Mosaico — adaptação da Palette Mosaic, com o desenho de ‘a’ do projeto.\n[url=https://github.com/shibuyafont/Palette-mosaic-font-mono]Palette Mosaic — Shibuya Font[/url] · SIL Open Font License 1.1\n[url=https://github.com/jpt/barlow]Barlow Condensed — Jeremy Tribby[/url] · SIL Open Font License 1.1\n\n[color=#dda63b][b]MÚSICA[/b][/color]\n[url=https://uppbeat.io/t/ian-aisling/empty-moon]Empty Moon — Ian Aisling / Uppbeat[/url]\n\n[color=#dda63b][b]REGISTRO DO PROJETO[/b][/color]\nFontes transcritas de Licencas_Assets / Registro_de_Licencas_Assets_ATUALIZADO.xlsx.\nOs comprovantes de origem e licença estão preservados junto ao projeto.\n"
	text.text = words
	content.add_child(text)
	first_button = Kit.button(content,"‹   VOLTAR",Rect2(72,753,240,60),func(): show_screen("home"),Kit.PAPER,true)
	Kit.label(content,"ROLE PARA VER TODOS OS CRÉDITOS  ↓",Rect2(958,765,570,34),23,Kit.GOLD,Kit.BOLD)
	_footer("↑ ↓ / RODA DO MOUSE  ROLAR       TAB  NAVEGAR       ESC  VOLTAR")

static func load_settings() -> ConfigFile:
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)
	return config

static func apply_settings() -> void:
	var config := load_settings()
	AudioServer.set_bus_volume_db(0,linear_to_db(float(config.get_value("audio","volume",0.8))))
	AudioServer.set_bus_mute(0,bool(config.get_value("audio","mute",false)))
	# Only override the project's window mode after an explicit saved preference.
	if config.has_section_key("video","fullscreen"):
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if bool(config.get_value("video","fullscreen")) else DisplayServer.WINDOW_MODE_WINDOWED)

func _save(section: String, key: String, value: Variant) -> void:
	var config := load_settings()
	config.set_value(section,key,value)
	var error := config.save(SETTINGS_PATH)
	if error != OK:
		_confirm("Não foi possível salvar", "Os ajustes desta sessão continuam ativos. Tente novamente ao reabrir o jogo.",Callable(),false)

func _settings() -> void:
	_header("DO SEU JEITO", "Prepare sua aventura.")
	Kit.rect(content,Rect2(72,255,1456,452),Color("2b1539"))
	Kit.label(content,"SOM",Rect2(104,282,400,48),35,Kit.GOLD,Kit.BOLD)
	Kit.label(content,"Volume geral",Rect2(105,351,400,45),29)
	var slider := HSlider.new()
	slider.position = Vector2(526,361)
	slider.size = Vector2(740,35)
	slider.max_value = 100
	slider.step = 1
	slider.value = float(load_settings().get_value("audio","volume",0.8))*100.0
	var track := StyleBoxFlat.new()
	track.bg_color = Kit.INK
	track.content_margin_top = 5
	track.content_margin_bottom = 5
	var fill := track.duplicate()
	fill.bg_color = Kit.GOLD
	slider.add_theme_stylebox_override("slider",track)
	slider.add_theme_stylebox_override("grabber_area",fill)
	slider.add_theme_stylebox_override("grabber_area_highlight",fill)
	var diamond: Texture2D = load("res://assets/ui/historiando/slider_diamond.svg")
	slider.add_theme_icon_override("grabber",diamond)
	slider.add_theme_icon_override("grabber_highlight",diamond)
	content.add_child(slider)
	var value := Kit.label(content,"%d%%" % slider.value,Rect2(1320,350,140,42),30,Kit.GOLD,Kit.BOLD)
	slider.value_changed.connect(func(v: float):
		value.text = "%d%%" % v
		AudioServer.set_bus_volume_db(0,linear_to_db(v/100.0))
		_save("audio","volume",v/100.0))
	_toggle("Silenciar áudio",Rect2(102,419,1350,53),bool(load_settings().get_value("audio","mute",false)),func(v: bool): AudioServer.set_bus_mute(0,v); _save("audio","mute",v))
	_toggle("Tela cheia",Rect2(102,513,1350,53),DisplayServer.window_get_mode() in [DisplayServer.WINDOW_MODE_FULLSCREEN,DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN],func(v: bool): DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if v else DisplayServer.WINDOW_MODE_WINDOWED); _save("video","fullscreen",v))
	_toggle("Reduzir animações da interface",Rect2(102,607,1350,53),bool(load_settings().get_value("accessibility","reduce_motion",false)),func(v: bool): _save("accessibility","reduce_motion",v))
	first_button = Kit.button(content,"‹   VOLTAR",Rect2(72,748,258,64),func(): show_screen(back_screen),Kit.PAPER,true)
	Kit.label(content,"Os ajustes são salvos automaticamente.",Rect2(947,762,580,37),24)
	_footer()

func _toggle(words: String, box: Rect2, value: bool, action: Callable) -> void:
	var check := CheckButton.new()
	check.position = box.position
	check.size = box.size
	check.text = words
	check.button_pressed = value
	check.add_theme_font_override("font",Kit.BODY)
	check.add_theme_font_size_override("font_size",29)
	check.add_theme_color_override("font_color",Kit.PAPER)
	check.add_theme_color_override("font_pressed_color",Kit.GOLD)
	check.add_theme_color_override("font_hover_pressed_color",Kit.GOLD)
	check.add_theme_color_override("font_focus_color",Kit.GOLD)
	content.add_child(check)
	check.toggled.connect(action)

func _about() -> void:
	_header("HISTORIANDO / PINDORAMA", "Histórias que atravessam o tempo.")
	Kit.brand(content,Rect2(95,304,310,300),true)
	Kit.label(content,"Uma aventura de exploração e descoberta",Rect2(495,296,980,62),42,Kit.GOLD,Kit.BOLD)
	var description := Kit.label(content,"Historiando é um jogo educacional sobre história e culturas dos povos originários, com exploração, narrativa e viagem temporal.\n\nIdentidade visual: artes originais do projeto Historiando.\nInterface: recortes de HQ, retículas e formas geométricas originais.\nTipografia: Historiando Mosaico, derivada de Palette Mosaic (Shibuya Font), e Barlow Condensed (Jeremy Tribby), sob SIL OFL.\nMúsica: Empty Moon, de Ian Aisling / Uppbeat.",Rect2(495,373,935,322),27)
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	first_button = Kit.button(content,"‹   VOLTAR",Rect2(72,748,258,64),func(): show_screen(back_screen),Kit.PAPER,true)
	Kit.button(content,"CONHECER A FONTE",Rect2(1037,748,490,64),func(): show_screen("type"),Kit.GOLD,true)
	_footer()

func _font_specimen() -> void:
	_header("TIPOGRAFIA / PRIMEIRA VERSÃO", "Historiando Mosaico")
	Kit.rect(content,Rect2(72,268,384,424),Kit.GOLD)
	Kit.label(content,"a",Rect2(145,240,260,330),268,Kit.INK,Kit.DISPLAY)
	Kit.label(content,"SEU DESENHO, EM VETOR",Rect2(99,614,340,41),24,Kit.INK,Kit.BOLD)
	Kit.label(content,"historiando",Rect2(510,259,970,104),77,Kit.PAPER,Kit.DISPLAY)
	Kit.label(content,"abcdefghijklmnopqrstuvwxyz",Rect2(517,417,970,60),36,Kit.PAPER,Kit.DISPLAY)
	Kit.label(content,"ABCDEFGHIJKLMNOPQRSTUVWXYZ",Rect2(517,493,1000,60),35,Kit.PAPER,Kit.DISPLAY)
	Kit.label(content,"á à â ã é ê í ó ô õ ú ü ç",Rect2(517,570,970,60),36,Kit.GOLD,Kit.DISPLAY)
	Kit.label(content,"0 1 2 3 4 5 6 7 8 9",Rect2(517,643,970,60),37,Kit.GOLD,Kit.DISPLAY)
	first_button = Kit.button(content,"‹   VOLTAR",Rect2(72,748,258,64),func(): show_screen("about"),Kit.PAPER,true)
	Kit.label(content,"Derivada de Palette Mosaic · versão 0.1 · SIL OFL",Rect2(762,763,775,40),24)
	_footer()

func _pause_menu() -> void:
	_header("PODE RESPIRAR.","A história espera por você.")
	Kit.brand(content,Rect2(1010,288,390,355),true)
	first_button = Kit.button(content,"CONTINUAR    ›",Rect2(95,304,635,89),func(): close_requested.emit())
	Kit.button(content,"AJUSTES",Rect2(95,418,635,78),func(): _open_settings("pause"),Kit.PAPER)
	Kit.button(content,"VOLTAR AO INÍCIO",Rect2(95,519,635,78),_confirm_home,Kit.CLAY)
	Kit.label(content,"Seu progresso de fases permanece salvo.",Rect2(101,632,700,50),27)
	_footer("ESC  CONTINUAR       ↑ ↓  NAVEGAR       ENTER  SELECIONAR")

func _demo() -> void:
	Kit.rect(content,Rect2(0,0,1600,900),Color(0.1,0,0.17,0.24))
	demo_hud = Hud.new()
	add_child(demo_hud)
	demo_hud.set_objective("Encontre os fragmentos pelo caminho.")
	demo_hud.set_interaction("Examinar descoberta")
	Kit.rect(content,Rect2(480,288,660,323),Kit.INK)
	Kit.label(content,"A AVENTURA EM CADA DETALHE",Rect2(507,307,610,40),25,Kit.GOLD,Kit.BOLD)
	Kit.label(content,"Experimente sua HUD",Rect2(507,353,610,63),47,Kit.PAPER,Kit.BOLD)
	Kit.label(content,"Demonstração visual · valores de exemplo",Rect2(507,420,610,40),24)
	first_button = Kit.button(content,"+ FRAGMENTO",Rect2(507,481,280,56),func(): demo_hud.set_collectibles(demo_hud.collectibles+1); demo_hud.notify("+1 FRAGMENTO  /  NOVA DESCOBERTA!"),Kit.GOLD,true)
	Kit.button(content,"TESTAR VIDAS",Rect2(809,481,280,56),func(): demo_hud.set_health((demo_hud.health+3)%4),Kit.CLAY,true)
	Kit.button(content,"‹   VOLTAR",Rect2(507,551,280,48),func(): show_screen("home"),Kit.PAPER,true)

func _retry_menu() -> void:
	_header("A JORNADA CONTINUA", "Toda descoberta tem seus desafios.")
	Kit.brand(content,Rect2(1030,286,355,340),true)
	Kit.label(content,"Vamos tentar de novo?",Rect2(96,295,820,90),55,Kit.GOLD,Kit.BOLD)
	Kit.label(content,"Recomece este cenário e encontre um novo caminho.",Rect2(99,392,820,50),29)
	first_button = Kit.button(content,"TENTAR NOVAMENTE    ›",Rect2(95,485,720,89),func(): restart_requested.emit())
	Kit.button(content,"VOLTAR AO INÍCIO",Rect2(95,604,720,78),func(): _launch("res://scenes/telaInicial/TelaInicial.tscn"); close_requested.emit(),Kit.PAPER)
	_footer("↑ ↓  NAVEGAR       ENTER  SELECIONAR")

func _launch_chapter(number: int) -> void:
	_launch(chapter_path(number))

static func chapter_path(number: int) -> String:
	return ISLAND_PATH if number == 1 else "res://scenes/menuDeFases/fase%d/fase_%d.tscn" % [number,number]

func _launch(path: String) -> void:
	if loading: return
	if not ResourceLoader.exists(path):
		_confirm("Caminho indisponível", "Não foi possível encontrar este cenário. Volte e escolha outro capítulo.",Callable(),false)
		return
	loading = true
	get_tree().paused = false
	var transition := get_node_or_null("/root/Transicao")
	if transition: transition.transicionar_para(path)
	else: get_tree().change_scene_to_file(path)

func _confirm_home() -> void:
	_confirm("Voltar ao início?", "O capítulo atual recomeçará. As fases concluídas continuam salvas.",func(): _launch("res://scenes/telaInicial/TelaInicial.tscn"); close_requested.emit())

func _confirm_exit() -> void:
	_confirm("Encerrar a aventura?", "Seu progresso de fases permanece salvo.",func(): get_tree().quit())

func _confirm(title: String, message: String, action: Callable, confirmation: bool = true) -> void:
	if is_instance_valid(modal): dismiss_modal()
	modal_focus = get_viewport().gui_get_focus_owner()
	modal_action = action
	# Block focus as well as pointer input behind the modal.
	for node in content.find_children("*","Control",true,false):
		var control := node as Control
		suspended_controls.append({"control":control,"focus":control.focus_mode})
		control.focus_mode = Control.FOCUS_NONE
	modal = Control.new()
	modal.name = "ComicModal"
	modal.size = Vector2(1600,900)
	modal.mouse_filter = Control.MOUSE_FILTER_STOP
	canvas.add_child(modal)
	Kit.rect(modal,Rect2(0,0,1600,900),Color("10001ddd"))
	var panel := ComicPanel.new()
	panel.position = Vector2(380,256)
	panel.size = Vector2(840,378)
	modal.add_child(panel)
	Kit.label(modal,"ANTES DE SEGUIR…",Rect2(422,281,710,36),24,Kit.CLAY,Kit.BOLD)
	Kit.label(modal,title,Rect2(420,331,747,71),49,Kit.INK,Kit.BOLD)
	var body := Kit.label(modal,message,Rect2(425,414,727,76),29,Kit.INK)
	body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var cancel := Kit.button(modal,"CANCELAR" if confirmation else "ENTENDI",Rect2(422,530,350,63),dismiss_modal,Kit.GOLD,true)
	if confirmation:
		var confirm := Kit.button(modal,"CONFIRMAR",Rect2(800,530,350,63),_accept_modal,Kit.CLAY,true)
		for property in ["focus_next","focus_previous","focus_neighbor_left","focus_neighbor_right","focus_neighbor_top","focus_neighbor_bottom"]:
			cancel.set(property,cancel.get_path_to(confirm))
			confirm.set(property,confirm.get_path_to(cancel))
	cancel.grab_focus()

func dismiss_modal() -> void:
	if not is_instance_valid(modal): return
	canvas.remove_child(modal)
	modal.queue_free()
	modal = null
	modal_action = Callable()
	for state in suspended_controls:
		if is_instance_valid(state.control): state.control.focus_mode = state.focus
	suspended_controls.clear()
	if is_instance_valid(modal_focus): modal_focus.grab_focus()

func _accept_modal() -> void:
	var action := modal_action
	dismiss_modal()
	if action.is_valid(): action.call()
