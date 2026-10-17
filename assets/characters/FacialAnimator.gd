extends Node
## Dialogue-driven visemes, blended reactions and short natural blinks.
## Facial shapes deform before skinning, so expressions follow the head rig.
var skin: MeshInstance3D
var skeleton: Skeleton3D
var original_mesh: Mesh
var automatic_blink := true
var external_blink: Callable
var blink_override: Callable
var mood := "curious"
var speaking := false
var mouth_peak := 0.0
var expression_changes := 0
var _targets := {}
var _weights := {}
var _text := ""
var _clock := 0.0
var _duration := 1.0
var _next_blink := 2.8
var _blink_clock := -1.0
const VISEMES := ["MouthOpen","MouthRound","VisemeWide","VisemeU","LipPress","LipBite"]

func configure(model: Node3D,cache: ArrayMesh = null) -> void:
	skeleton = model.find_child("Skeleton3D",true,false)
	for node: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		if node.mesh and (node.mesh.get_blend_shape_count()>0 or cache!=null and node.name=="Yara_PaintedSkin"):
			skin = node
			break
	if skin==null or skeleton==null:
		push_error("Facial animation requires a skinned face with expression shapes")
		return
	original_mesh = skin.mesh
	if cache!=null:
		var mesh := ArrayMesh.new()
		mesh.blend_shape_mode = cache.blend_shape_mode
		for i in cache.get_blend_shape_count(): mesh.add_blend_shape(cache.get_blend_shape_name(i))
		for surface in cache.get_surface_count():
			var arrays := cache.surface_get_arrays(surface)
			var previous := original_mesh.surface_get_arrays(surface)
			# Preserve the waking overlay's eye coordinates and material overrides.
			if previous[Mesh.ARRAY_TEX_UV2]!=null: arrays[Mesh.ARRAY_TEX_UV2] = previous[Mesh.ARRAY_TEX_UV2]
			mesh.add_surface_from_arrays(cache.surface_get_primitive_type(surface),arrays,cache.surface_get_blend_shape_arrays(surface))
			mesh.surface_set_material(surface,cache.surface_get_material(surface))
		skin.mesh = mesh
	for i in skin.mesh.get_blend_shape_count():
		var shape := str(skin.mesh.get_blend_shape_name(i))
		_weights[shape] = 0.0
		_targets[shape] = 0.0
	set_mood("curious")

func set_mood(value: String) -> void:
	mood = value
	expression_changes += 1
	for shape in _targets: _targets[shape] = 0.0
	match value:
		"curious":
			_targets["BrowUp"] = .48
			_targets["BrowAsym"] = .22
		"amused":
			_targets["Grin"] = .78
			_targets["CheekRaise"] = .25
			_targets["BrowAsym"] = .8
		"surprised":
			_targets["BrowUp"] = 1.0
			_targets["MouthOpen"] = .90
			_targets["MouthRound"] = .12
			_targets["EyesWide"] = 1.0
		"confused":
			_targets["Concern"] = .6
			_targets["BrowAsym"] = 1.0
			_targets["Squint"] = .40
		"reassuring":
			_targets["Smile"] = .65
			_targets["CheekRaise"] = .35
			_targets["BrowUp"] = .30
		"determined":
			_targets["Smirk"] = .6
			_targets["Squint"] = .25
			_targets["BrowAsym"] = .35

func speak(words: String) -> void:
	var tags := RegEx.new()
	tags.compile("\\[[^\\]]*\\]")
	_text = tags.sub(words,"",true).to_lower()
	_clock = 0.0
	_duration = clampf(_text.length()*.045,1.2,5.3)
	speaking = true

func stop_speaking() -> void:
	speaking = false

func _process(delta: float) -> void:
	if skin==null: return
	_clock += delta
	var speech := {}
	if speaking and _clock<_duration and not _text.is_empty():
		var index := mini(int(_clock/_duration*_text.length()),_text.length()-1)
		var letter := _text.substr(index,1)
		var pulse := .65+.30*absf(sin(_clock*11.8))
		if letter in "aáãâ": speech["MouthOpen"] = pulse
		elif letter in "eéiíê": speech["VisemeWide"] = pulse
		elif letter in "oóôõ": speech["MouthRound"] = pulse
		elif letter in "uúw": speech["VisemeU"] = pulse
		elif letter in "bmp": speech["LipPress"] = .9
		elif letter in "fv": speech["LipBite"] = .85
		elif not letter in [" ",".",",","!","?",":",";","…"]:
			speech["VisemeWide"] = .32
			speech["MouthOpen"] = .15
	elif speaking: speaking = false
	# Speaking shapes alternate vowels; a surprised listener holds a small O.
	var blink := 0.0
	if automatic_blink:
		_next_blink -= delta
		if _next_blink<=0:
			_blink_clock = 0.0
			_next_blink = 3.1+.35*sin(_clock)
		if _blink_clock>=0:
			_blink_clock += delta
			blink = smoothstep(0,.055,_blink_clock) if _blink_clock<.105 else 1-smoothstep(.105,.195,_blink_clock)
			if _blink_clock>.195: _blink_clock = -1
	if blink_override.is_valid(): blink = maxf(blink,float(blink_override.call()))
	for shape in _weights:
		var target: float = _targets.get(shape,0.0)
		if speaking and shape in VISEMES: target = speech.get(shape,0.0)
		if speaking and shape in ["Grin","Smile","Concern","Smirk"]: target *= .38
		if shape=="Blink": target = blink
		if shape=="Blink" and external_blink.is_valid(): target = 0.0
		_weights[shape] = lerpf(_weights[shape],target,1-exp(-delta*(60 if shape=="Blink" else 18)))
		var index := skin.find_blend_shape_by_name(shape)
		if index>=0: skin.set_blend_shape_value(index,_weights[shape])
	if external_blink.is_valid(): external_blink.call(blink)
	mouth_peak = maxf(mouth_peak,_weights.get("MouthOpen",0.0))

func release() -> void:
	set_process(false)
	if skin:
		for i in skin.mesh.get_blend_shape_count(): skin.set_blend_shape_value(i,0)
		skin.mesh = original_mesh
