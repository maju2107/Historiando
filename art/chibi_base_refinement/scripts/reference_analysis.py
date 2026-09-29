"""Read source pixels; report measurable dimensions, without altering images."""
import bpy,json
import numpy as np
from config import PROJECT,REFERENCES,PREFIX,REFERENCE_ALIGNMENT

def pixels(path):
    im=bpy.data.images.load(str(path),check_existing=True)
    w,h=im.size; data=np.empty(w*h*4,dtype=np.float32); im.pixels.foreach_get(data)
    return data.reshape(h,w,4)[::-1,:,:3],im

def measure_references():
    report={'method':'Orthographic full-body views define dimensions. Closeups constrain details only.',
            'inspected_categories':list(REFERENCES),'images':{},'measurements':{}}
    for category,suffix in REFERENCES.items():
        path=PROJECT/'references'/(PREFIX+suffix+'.jpg')
        rgb,im=pixels(path); bg=np.median(rgb[10:50,10:50,:],axis=(0,1))
        mask=np.max(np.abs(rgb-bg),axis=2)>.022
        yy,xx=np.where(mask)
        report['images'][category]={'file':path.name,'size':list(im.size),
          'foreground_bbox_px':[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]}
        if category not in REFERENCE_ALIGNMENT: continue
        setup=REFERENCE_ALIGNMENT[category]; floor=setup['floor_y_px']; height=setup['height_px']; center=setup['center_x_px']
        sections=[]
        for z in (.025,.07,.12,.18,.213,.27,.32,.35,.39,.43,.48,.53,.559,.61,.64,.67,.70,.74,.78,.82,.86,.90,.94,.97):
            row=int(round(floor-z*height)); xs=np.where(np.any(mask[max(0,row-1):row+2],axis=0))[0]
            if len(xs): sections.append({'z_m':z,'min_px':int(xs.min()),'max_px':int(xs.max()),
                  'min_m':float((xs.min()-center)/height),'max_m':float((xs.max()-center)/height),
                  'width_m':float((xs.max()-xs.min())/height)})
        report['measurements'][category]={'sections':sections,'pixels_per_meter':height}
    report['landmarks']={
      'total_height_m':1.0,'head_top_z_m':1.0,'chin_z_m':(914-390)/823,
      'head_height_m':(390-92)/823,'heads_tall_measured':823/(390-92),
      'eye_centers_front_px':[[639,263],[765,263]],'eye_diameter_px':70,
      'eye_center_z_m':(914-263)/823,'eye_center_spacing_m':126/823,
      'eye_diameter_m':70/823,'nose_center_z_m':(914-295)/823,'mouth_center_z_m':(914-330)/823,
      'shoulder_z_m':(914-452)/823,'crotch_z_m':(914-634)/823,'knee_z_m':(914-739)/823,
      'note':'The images measure about 2.76 heads tall, close to three. Image proportions take precedence over imposing 3.5 heads.'}
    (PROJECT/'references'/'analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
