# Editing the island speeches in Dialogic

The opening uses native Dialogic timelines. The speech wording is stored in
these files, rather than in the cutscene script:

- `res://dialogo/linha_do_tempo/ilha_despertar.dtl`: Yara waking up.
- `res://dialogo/linha_do_tempo/kai_encontro.dtl`: Kai and Yara's conversation.

In Godot, open the **Dialogic** tab, choose **Timelines**, and open either
timeline. Select a **Text** event, edit its speech, and save with **Ctrl+S**.
You can also double-click the `.dtl` file in the FileSystem dock to open its
Dialogic editor. Start a fresh game run to replay the opening with the edits.

In `CenarioIlha.tscn`, select **Opening**. Its Inspector section
**Diálogos / Dialogic** exposes **Waking Dialogue** and **Kai Dialogue**.
These point to the two timelines above; you can assign another Dialogic
timeline there without editing code.

Keep the **Signal** events between speeches: they trigger the matching camera
shots, gestures, expressions, effects and mission handoff. Edit the Text events
to change only the speeches. Keep existing `[b]...[/b]` tags where you want the
same bold emphasis. The current banner style and manual advance behavior are
shared by both timelines and do not need changing to edit the words.
