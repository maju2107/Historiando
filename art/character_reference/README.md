# Character reference model

Open `Character_Reference.blend` in Blender. The supplied character sheet is packed into the file, so it does not depend on the original image remaining in Downloads.

The model includes a shaped chibi head, layered amber eyes, eyebrows and baby hairs, a pulled-back scalp section, a voluminous ponytail made from editable curl clumps, white hair ribbons, a purple short-sleeved jumpsuit, gold buttons, white drawstrings, and tooth-pattern platform shoes.

## Editing

- `01_BODY`: head and simplified body parts beneath the clothes.
- `02_FACE`: eye layers, lashes, brows, nose and mouth.
- `03_HAIR`: scalp, swept locks, ponytail volume, curl clumps and curl ridges.
- `04_OUTFIT`: torso, sleeves, continuous trousers, seams, buttons and cords.
- `05_SHOES`: uppers, soles, eye appliques and decorative teeth.
- `06_RIBBON`: gold tie, bow loops and hanging ribbons.
- `REFERENCES`: packed front/side reference images. Initially hidden; enable the collection in the Outliner to display them in orthographic views.
- `STUDIO`: camera, lights and floor used for the previews.

Most parts are meshes; hair ridges, seams, mouth and ribbons include editable curves. Subdivision and bevel modifiers remain available on relevant parts. No add-ons or particle simulation are required.

This is a static, stylized interpretation of the drawing. It is not rigged or animation-ready. Body components and garment pieces are separate, and the concealed body is a simplified blockout. Retopology, mesh joining where needed, UV layout and rigging would be separate production steps.

## Previews

`three_quarter.png`, `front.png`, `side.png` and `back.png` show the model under studio lighting. The latter three use a slight downward camera angle to show the shoes and volume.

## Rebuilding

`build_character.py` recreates the model and renders from scratch. Run Blender in background mode with this script from the Historiando project root. Rebuilding overwrites the generated blend and preview images, so save manual edits under a different filename first. The script uses the original reference location in Downloads; the saved blend itself uses a packed copy.

