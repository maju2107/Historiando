"""Incremental milestone driver. It resumes saved geometry, never rebuilds it."""
import sys,argparse,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from config import *
from helpers import *

def run_milestone(number):
    ensure_directories()
    dest=PROJECT/'output'/f'{number:02d}_{MILESTONES[number]}.blend'
    if dest.exists():
        print('EXISTING CHECKPOINT PRESERVED',dest); return
    if number==1:
        setup_scene(); setup_references()
        from reference_analysis import measure_references
        report=measure_references()
        render_validation_views(1)
        save_project(1,'Continued existing .blend. Classified all nine references, aligned primary images, measured proportions, normalized height to 1 m, created four orthographic cameras. Geometry retained.')
    else:
        load_checkpoint(number-1)
        from modeling import apply_milestone
        notes=apply_milestone(number)
        render_validation_views(number,final=number>=6)
        save_project(number,notes)
        if number==7:
            from delivery import export_final
            export_final()

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser(); parser.add_argument('--milestone',type=int,required=True,choices=range(1,8))
    run_milestone(parser.parse_args(args).milestone)
