@tool
extends Label

@onready var anim: AnimationPlayer = $"../AnimationPlayer"

func _ready() -> void:
  if not resized.is_connected(_center_pivot):
    resized.connect(_center_pivot)

  call_deferred("_center_pivot")

  # Only run animation during the actual game, not in the editor
  if not Engine.is_editor_hint():
    await get_tree().process_frame
    anim.play("active")


func _notification(what: int) -> void:
  if what == NOTIFICATION_RESIZED:
    call_deferred("_center_pivot")


func _center_pivot() -> void:
  pivot_offset = size / 2
