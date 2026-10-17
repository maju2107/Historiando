extends Control
signal fragments_completed
## Reusable HUD. Call set_health, set_collectibles, set_objective and
## set_interaction from the relevant gameplay systems.
const Kit = preload("res://scenes/ui/ui_kit.gd")
var canvas: Control
var hearts: Label
var pause_button: Button
var pause_prompt: TextureRect
var location_label: Label
var activity_label: Label
var objective: Label
var objective_summary: Label
var journey_heading: Label
var objective_panel: PanelContainer
var interaction: Control
var prompt: Label
var notification: Label
var notice_timer: Timer
var checkpoint_notification: Label
var checkpoint_notice_timer: Timer
var epoch_presentation: PanelContainer
var health := 3
var collectibles := 0
var fragment_goal := 0
var fragment_mission: VBoxContainer
var fragment_count: Label
var fragment_bar: ProgressBar
var fragments_complete := false
var _cinematic_visibility := {}
var _objective_position := Vector2.ZERO

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	canvas = Control.new()
	canvas.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(canvas)
	Kit.rect(canvas, Rect2(43,43,350,103), Kit.INK)
	Kit.rect(canvas, Rect2(48,48,340,93), Kit.PAPER)
	Kit.brand(canvas, Rect2(58,53,78,78), true)
	Kit.label(canvas,"YARA",Rect2(150,53,200,25),20,Kit.INK,Kit.BOLD)
	hearts = Kit.label(canvas,"",Rect2(148,76,220,48),34,Kit.CLAY,Kit.BOLD)
	Kit.rect(canvas,Rect2(46,158,340,7),Kit.INK)
	Kit.rect(canvas,Rect2(46,158,340,4),Kit.GOLD)
	pause_button = Kit.button(canvas,"II   PAUSA",Rect2(1360,48,192,64),_pause,Kit.PAPER,true)
	pause_button.name = "PauseButton"
	pause_button.focus_mode = Control.FOCUS_NONE
	pause_button.tooltip_text = "Pausar (Y / Esc)"
	pause_prompt = Kit.texture(pause_button,"res://assets/ui/historiando/controls/button_y.svg",Rect2(157,34,46,46))
	pause_prompt.name = "PauseYPrompt"
	location_label = Kit.label(canvas,"PLEISTOCENO",Rect2(665,42,300,26),21,Kit.PAPER,Kit.BOLD)
	location_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	activity_label = Kit.label(canvas,"EXPLORAÇÃO",Rect2(665,68,300,24),16,Kit.PAPER)
	activity_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	objective_panel = PanelContainer.new()
	objective_panel.name = "MissionPanel"
	objective_panel.position = Vector2(46,204)
	objective_panel.size = Vector2(328,0)
	objective_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = Color("1a002ce8")
	panel_style.border_width_left = 5
	panel_style.border_color = Kit.GOLD
	panel_style.content_margin_left = 19
	panel_style.content_margin_right = 20
	panel_style.content_margin_top = 12
	panel_style.content_margin_bottom = 18
	objective_panel.add_theme_stylebox_override("panel",panel_style)
	canvas.add_child(objective_panel)
	var mission_content := VBoxContainer.new()
	mission_content.add_theme_constant_override("separation",8)
	objective_panel.add_child(mission_content)
	journey_heading = Kit.label(mission_content,"SUA JORNADA",Rect2(),20,Kit.GOLD,Kit.BOLD)
	objective = Kit.label(mission_content,"Explore os caminhos da ilha.",Rect2(),25)
	objective.custom_minimum_size.x = 287
	objective.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	objective_summary = Kit.label(mission_content,objective.text,Rect2(),25)
	objective_summary.custom_minimum_size.x = 287
	objective_summary.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	objective_summary.clip_text = true
	objective_summary.hide()
	fragment_mission = VBoxContainer.new()
	fragment_mission.name = "ReturnHomeMission"
	fragment_mission.add_theme_constant_override("separation",7)
	mission_content.add_child(fragment_mission)
	fragment_mission.add_child(HSeparator.new())
	Kit.label(fragment_mission,"DE VOLTA PARA CASA",Rect2(),18,Kit.GOLD,Kit.BOLD)
	fragment_count = Kit.label(fragment_mission,"",Rect2(),23,Kit.PAPER,Kit.BOLD)
	fragment_bar = ProgressBar.new()
	fragment_bar.custom_minimum_size = Vector2(0,9)
	fragment_bar.show_percentage = false
	var track := StyleBoxFlat.new()
	track.bg_color = Color("100019")
	var fill := StyleBoxFlat.new()
	fill.bg_color = Kit.GOLD
	fragment_bar.add_theme_stylebox_override("background",track)
	fragment_bar.add_theme_stylebox_override("fill",fill)
	fragment_mission.add_child(fragment_bar)
	fragment_mission.hide()
	interaction = Control.new()
	interaction.position = Vector2(585,720)
	interaction.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(interaction)
	Kit.rect(interaction,Rect2(0,0,430,65),Kit.INK)
	Kit.rect(interaction,Rect2(8,8,49,49),Kit.GOLD)
	Kit.label(interaction,"E",Rect2(8,8,49,49),30,Kit.INK,Kit.BOLD).horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	prompt = Kit.label(interaction,"Interagir",Rect2(74,10,343,45),28)
	interaction.hide()
	notification = Kit.label(canvas,"",Rect2(505,156,590,63),30,Kit.INK,Kit.BOLD)
	notification.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	notification.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var bg := preload("res://scenes/ui/comic_panel.gd").new()
	bg.fill = Kit.GOLD
	bg.size = Vector2(620,69)
	bg.position = Vector2(-15,-3)
	bg.show_behind_parent = true
	notification.add_child(bg)
	notification.hide()
	notice_timer = Timer.new()
	notice_timer.one_shot = true
	notice_timer.timeout.connect(notification.hide)
	add_child(notice_timer)
	# Checkpoints use a viewport-relative bottom row, clear of quiz speech.
	checkpoint_notification = Kit.label(self,"",Rect2(),30,Kit.INK,Kit.BOLD)
	checkpoint_notification.name = "CheckpointNotice"
	checkpoint_notification.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	checkpoint_notification.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var checkpoint_bg := preload("res://scenes/ui/comic_panel.gd").new()
	checkpoint_bg.name = "Panel"
	checkpoint_bg.fill = Kit.GOLD
	checkpoint_bg.show_behind_parent = true
	checkpoint_notification.add_child(checkpoint_bg)
	checkpoint_notification.hide()
	checkpoint_notice_timer = Timer.new()
	checkpoint_notice_timer.one_shot = true
	checkpoint_notice_timer.timeout.connect(checkpoint_notification.hide)
	add_child(checkpoint_notice_timer)
	epoch_presentation = preload("res://scenes/ui/epoch_presentation.gd").new()
	canvas.add_child(epoch_presentation)
	set_health(health)
	set_collectibles(collectibles)
	get_viewport().size_changed.connect(_resize)
	_resize()

func _resize() -> void:
	var viewport := get_viewport_rect().size
	var factor := minf(viewport.x/1600.0,viewport.y/900.0)
	canvas.scale = Vector2.ONE*factor
	canvas.position = (viewport-Vector2(1600,900)*factor)/2
	# Keep the pause target usable even on a short landscape phone screen.
	var target_scale := maxf(1.0,48.0/(64.0*factor))
	pause_button.scale = Vector2.ONE*target_scale
	pause_button.position = Vector2((viewport.x-canvas.position.x)/factor-48-192*target_scale,48)
	# On short phones the mission keeps its current step and fragment progress
	# above the joystick; its complete instructions remain in the label/tooltip.
	var compact_mission := viewport.y < 550 and viewport.x > viewport.y
	journey_heading.visible = not compact_mission
	objective.visible = not compact_mission
	objective_summary.visible = compact_mission
	objective_panel.reset_size()
	var notice_factor := clampf(viewport.x/1600.0,.65,1.1)
	checkpoint_notification.size = Vector2(minf(620*notice_factor,viewport.x-40),52*notice_factor)
	checkpoint_notification.position = Vector2((viewport.x-checkpoint_notification.size.x)/2,viewport.y-checkpoint_notification.size.y-20)
	checkpoint_notification.add_theme_font_size_override("font_size",roundi(29*notice_factor))
	checkpoint_notification.get_node("Panel").size = checkpoint_notification.size+Vector2(16,4)
	checkpoint_notification.get_node("Panel").position = Vector2(-8,-2)

func _process(_delta: float) -> void:
	pause_prompt.visible = not Kit.uses_touch_controls(get_tree())

func set_health(value: int, maximum: int = 3) -> void:
	health = clampi(value,0,maximum)
	if hearts:
		hearts.text = "VIDAS  " + "● ".repeat(health) + "○ ".repeat(maximum-health)

func set_collectibles(value: int) -> void:
	collectibles = maxi(value,0)
	_update_fragment_mission()

func set_fragment_goal(total: int) -> void:
	fragment_goal = maxi(total,0)
	_update_fragment_mission()

func _update_fragment_mission() -> void:
	if fragment_mission == null: return
	fragment_mission.visible = fragment_goal > 0
	if fragment_goal <= 0: return
	fragment_count.text = "Fragmentos  %02d / %02d" % [mini(collectibles,fragment_goal),fragment_goal]
	fragment_bar.max_value = fragment_goal
	fragment_bar.value = mini(collectibles,fragment_goal)
	if collectibles >= fragment_goal and not fragments_complete:
		fragments_complete = true
		fragment_count.text += "  ✓"
		notify("TODOS OS FRAGMENTOS REUNIDOS!")
		fragments_completed.emit()
	elif fragments_complete:
		fragment_count.text += "  ✓"
	objective_panel.reset_size()

func set_cinematic_mission_only(enabled: bool) -> void:
	if enabled and _cinematic_visibility.is_empty():
		_objective_position = objective_panel.position
		for child in canvas.get_children():
			if child is CanvasItem:
				_cinematic_visibility[child] = child.visible
				child.visible = child == objective_panel
		objective_panel.position.y += 100
	elif not enabled and not _cinematic_visibility.is_empty():
		for child in _cinematic_visibility:
			if is_instance_valid(child): child.visible = _cinematic_visibility[child]
		_cinematic_visibility.clear()
		objective_panel.position = _objective_position

func set_objective(text: String) -> void:
	if objective:
		objective.text = text
		objective.tooltip_text = text
		objective_summary.text = text.get_slice("\n",0)
		objective_summary.tooltip_text = text
		# Containers grow with wrapped text and can shrink for a shorter mission.
		objective_panel.reset_size()

func set_location(location: String,activity: String = "EXPLORAÇÃO") -> void:
	location_label.text = location
	activity_label.text = activity

func set_interaction(text: String, key: String = "E") -> void:
	if not interaction: return
	prompt.text = text
	(interaction.get_child(2) as Label).text = key
	interaction.visible = not text.is_empty()

func notify(text: String) -> void:
	notification.text = text
	notification.show()
	notice_timer.start(3.0)

func notify_checkpoint(text: String) -> void:
	checkpoint_notification.text = text
	checkpoint_notification.show()
	checkpoint_notice_timer.start(3.0)

func show_epoch_intro() -> void:
	epoch_presentation.present()

func _pause() -> void:
	var manager := get_node_or_null("/root/BotaoGlobal")
	if manager and manager.has_method("toggle_pause"): manager.toggle_pause()
