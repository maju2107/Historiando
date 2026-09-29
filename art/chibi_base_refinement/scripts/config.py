"""Refinement controls. This project starts only from the user's FBX."""
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
SOURCE=Path('C:/Users/obran/Downloads/base.fbx')
REFERENCE_SOURCE=Path('C:/Users/obran/OneDrive/Área de Trabalho/referencias')
PREFIX='cartoon-female-chibi-character-base-mesh-3d-model-'
TOTAL_HEIGHT=1.0
HEAD_HEIGHT=.363
HEAD_WIDTH=.350
HEAD_DEPTH=.340
EYE_DIAMETER=.085
EYE_SPACING=.153
EYE_HEIGHT=.791
MOUTH_HEIGHT=.710
NECK_WIDTH=.064
SHOULDER_HEIGHT=.561
WAIST_WIDTH=.128
HIP_WIDTH=.190
CROTCH_HEIGHT=.341
KNEE_HEIGHT=.213
FOOT_WIDTH=.139
FOOT_LENGTH=.180
ARM_REACH=.465
REFERENCES={'FRONT':'9a858a9e65','SIDE':'21b9f05615','BACK':'b0b62758aa',
 'THREE_QUARTER_FRONT':'7e135165fc','THREE_QUARTER_BACK':'93d81549c6',
 'FACE_CLOSEUP_FRONT':'5f5cf94e96','FACE_CLOSEUP_THREE_QUARTER':'2aa77f1153',
 'TOP_ANGLED':'3726ebacab','CONTACT_SHEET':'61135f677f'}
STAGES={1:'import_cleanup',2:'reference_setup',3:'proportion_fix',4:'head_refine',
        5:'topology_cleanup',6:'hands_feet',7:'validation'}
REFERENCE_ALIGNMENT={view:{'center_x_px':698 if view=='SIDE' else 702,
 'floor_y_px':914,'height_px':823,'offset':(0,0,0)} for view in ('FRONT','SIDE','BACK')}
