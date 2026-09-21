import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from helpers import load_checkpoint
from cleanup import final_cleanup
from validation import validate_scene
load_checkpoint(6)
print(final_cleanup())
validate_scene(7,strict=True)
