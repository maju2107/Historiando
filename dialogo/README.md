# Editing the island speeches in Dialogic

The opening and ending use native Dialogic timelines. The speech wording is stored in
these files, rather than in the cutscene script:

- `res://dialogo/linha_do_tempo/ilha_despertar.dtl`: Yara waking up.
- `res://dialogo/linha_do_tempo/kai_encontro.dtl`: Kai and Yara's conversation.
- `res://dialogo/linha_do_tempo/ilha_final.dtl`: the all-fragment ending and goodbye.

In Godot, open the **Dialogic** tab, choose **Timelines**, and open any
timeline. Select a **Text** event, edit its speech, and save with **Ctrl+S**.
You can also double-click the `.dtl` file in the FileSystem dock to open its
Dialogic editor. Start a fresh game run to replay the opening with the edits.

In `CenarioIlha.tscn`, select **Opening**. Its Inspector section
**Diálogos / Dialogic** exposes **Waking Dialogue** and **Kai Dialogue**.
These point to the two timelines above; you can assign another Dialogic
timeline there without editing code.

For the finale, select **Ending** and edit its **Ending Dialogue** resource.
It starts once all island fragments have been collected. The new `end_*`
Signal events control the portal reveal, reaction shots and goodbye, while the
Text events contain every spoken line. The current **Clearing Position** is
an open part of the island used for unobstructed staging.

Keep the **Signal** events between speeches: they trigger the matching camera
shots, gestures, expressions, effects and mission handoff. Edit the Text events
to change only the speeches. Keep existing `[b]...[/b]` tags where you want the
same bold emphasis. The current banner style and manual advance behavior are
shared by all three timelines and do not need changing to edit the words.

The parkour also uses `quiz_gelo.dtl`, `quiz_megafauna.dtl`, `quiz_clima.dtl`
and `quiz_humanos.dtl` for Kai's hints after nonfatal wrong answers. Edit their
Text events in the same Dialogic editor. The question/answer wording itself is
in `res://_testes/cenario_ilha/parkour/pleistocene_questions.tres`, exposed as
**Question Bank** on **ParkourFlutuante**. See that folder's `QUIZ.md`.
