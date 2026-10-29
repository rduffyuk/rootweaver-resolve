# Atlas architecture assets

These views use Rootweaver's approved Atlas visual language: warm paper, violet
actions, muted dotted results, line icons, generous spacing and labelled boundaries.
The renderer adapts the existing Atlas text, icon, palette and arrow conventions
to this standalone project. No platform architecture asset was replaced.

The owning explanation is [ARCHITECTURE.md](../ARCHITECTURE.md). Open
[index.html](index.html) locally for all three views with replay/still controls.
On small screens, each diagram can be panned without shrinking its text. Native
SVG image embeds are used in Markdown; if a viewer suppresses animation, open the
SVG directly or use its `.static.svg` companion. Host-specific SVG proxy behaviour
is separate from the local Chrome checks.

`models.json` owns geometry, labels and relationships. The `.mmd` files are editable
logical companions. Generate native animated and static SVGs without dependencies:

```sh
python scripts/render_architecture.py
```

`manifest.json` binds the renderer, source model and six exports. Animation moves
only along connectors, runs for 4.8 seconds and then stops. Reduced-motion and
print modes suppress motion. Direction and labels never depend on animation.
No external fonts, scripts, network resources or telemetry are loaded.

| View | State shown | Question answered |
|---|---|---|
| Investigation loop | Historical lab implementation / retained evidence | Who chooses a check, who executes it, and what can a human inspect? |
| Packet investigation | Actual retained sequence | What did the tools establish, and what still needs investigation? |
| Standalone paths | Current shipped source | What runs locally, and what happens only after explicit fresh-inference opt-in? |

Architecture meaning and diagram legibility are reviewed separately from owner
acceptance. These images do not qualify production behaviour or change historical
evaluation outcomes.
