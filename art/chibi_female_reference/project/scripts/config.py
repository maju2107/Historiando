"""Dimensions in meters; image alignment and modeling controls live here."""
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
SOURCE_BLEND=PROJECT.parent/'Chibi_Feminina.blend'
REFERENCE_SOURCE=Path('C:/Users/obran/OneDrive/Área de Trabalho/referencias')
PREFIX='cartoon-female-chibi-character-base-mesh-3d-model-'
TOTAL_HEIGHT=1.0
HEAD_HEIGHT=.365
HEAD_WIDTH=.350
HEAD_DEPTH=.340
EYE_DIAMETER=.090
EYE_SPACING=.155
SHOULDER_WIDTH=.170
SHOULDER_HEIGHT=.559
TORSO_LENGTH=.211
WAIST_WIDTH=.128
HIP_WIDTH=.185
LEG_LENGTH=.341
KNEE_HEIGHT=.213
FOOT_WIDTH=.139
FOOT_LENGTH=.190
ARM_LENGTH=.310
HAND_LENGTH=.153
FINGERS_PER_HAND=4
PREVIEW_RESOLUTION=900
FINAL_RESOLUTION=1400
REFERENCE_OPACITY=.45
REFERENCE_DISTANCE=.35
REFERENCE_ALIGNMENT={
 'FRONT':{'center_x_px':702.0,'floor_y_px':914.0,'height_px':823.0,'offset':(0,0,0)},
 'SIDE':{'center_x_px':698.0,'floor_y_px':914.0,'height_px':823.0,'offset':(0,0,0)},
 'BACK':{'center_x_px':702.0,'floor_y_px':914.0,'height_px':823.0,'offset':(0,0,0)},
}
REFERENCES={
 'FRONT':'9a858a9e65', 'SIDE':'21b9f05615', 'BACK':'b0b62758aa',
 'THREE_QUARTER_FRONT':'7e135165fc','THREE_QUARTER_BACK':'93d81549c6',
 'FACE_CLOSEUP_FRONT':'5f5cf94e96','FACE_CLOSEUP_THREE_QUARTER':'2aa77f1153',
 'TOP_ANGLED':'3726ebacab','CONTACT_SHEET':'61135f677f',
}
MILESTONES={1:'reference_setup',2:'silhouette_blockout',3:'production_topology',
            4:'face_and_ears',5:'hands_and_feet',6:'validation_comparison',7:'final_cleanup'}
