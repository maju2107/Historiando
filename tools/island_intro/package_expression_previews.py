"""Assemble actual engine captures; no generated or retouched character images."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];P=R/'art/island_intro/previews'
font=ImageFont.truetype(str(R/'common/fonts/historiando/BarlowCondensed-Medium.ttf'),20)
title=ImageFont.truetype(str(R/'common/fonts/historiando/BarlowCondensed-Bold.ttf'),28)
poses=[('Neutral','Neutral'),('TalkA','A / open'),('TalkE','E / I'),('TalkO','O / rounded'),('TalkU','U / pucker'),('Amused','Amused'),('Smile','Smile'),('Surprised','Surprised'),('Confused','Confused'),('Closed','M / B / P'),('Bite','F / V'),('Blink','Blink')]
sheet=Image.new('RGB',(1800,1380),'#171a1c');draw=ImageDraw.Draw(sheet)
for actor,who in enumerate(['Kai','Yara']):
 top=actor*690;draw.text((12,top+4),who.upper()+' | Speech shapes and reactions',font=title,fill='#dac7a7')
 for index,(name,label) in enumerate(poses):
  x=(index%6)*300;y=top+40+(index//6)*325
  draw.text((x+10,y),label,font=font,fill='#dda63b')
  frame=Image.open(P/'expressions'/f'{who}_{name}.png').convert('RGB').resize((300,300),Image.Resampling.LANCZOS)
  sheet.paste(frame,(x,y+25))
sheet.save(P/'expressions.png')
motion=Path('C:/Users/obran/Historiando_Backups/kai_rig_2026-10-16/dialogue_motion')
frames=[Image.open(path).convert('RGB') for cue in ['yara_console','kai_correct'] for path in sorted(motion.glob(cue+'_*.png'))]
if len(frames)==40:
 frames[0].save(P/'dialogue_motion.gif',save_all=True,append_images=frames[1:],duration=90,loop=0,optimize=False)
print('Packaged expression sheet and live dialogue captures')
