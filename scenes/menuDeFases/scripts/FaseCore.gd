extends Node

signal progresso_alterado

const SAVE_PATH := "user://progresso.cfg"

var fase1_concluida := false
var fase2_concluida := false
var fase3_concluida := false

func _ready() -> void:
	carregar_progresso()

func concluir_fase(numero_da_fase: int) -> void:
	match numero_da_fase:
		1:
			fase1_concluida = true
		2:
			fase2_concluida = true
		3:
			fase3_concluida = true
		_:
			push_warning("Tentativa de concluir uma fase inexistente: %d" % numero_da_fase)
			return

	salvar_progresso()
	progresso_alterado.emit()

func salvar_progresso() -> void:
	var config := ConfigFile.new()
	config.set_value("fases", "fase_1_concluida", fase1_concluida)
	config.set_value("fases", "fase_2_concluida", fase2_concluida)
	config.set_value("fases", "fase_3_concluida", fase3_concluida)

	var erro := config.save(SAVE_PATH)
	if erro != OK:
		push_error("Não foi possível salvar o progresso (erro %d)." % erro)

func carregar_progresso() -> void:
	var config := ConfigFile.new()
	var erro := config.load(SAVE_PATH)
	if erro == ERR_FILE_NOT_FOUND:
		return
	if erro != OK:
		push_warning("Não foi possível carregar o progresso (erro %d)." % erro)
		return

	fase1_concluida = bool(config.get_value("fases", "fase_1_concluida", false))
	fase2_concluida = bool(config.get_value("fases", "fase_2_concluida", false))
	fase3_concluida = bool(config.get_value("fases", "fase_3_concluida", false))

func resetar_progresso() -> void:
	fase1_concluida = false
	fase2_concluida = false
	fase3_concluida = false
	salvar_progresso()
	progresso_alterado.emit()
