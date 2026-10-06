# PatternFerry: native-first feasibility

**Experimental feasibility study for LMMS 1.3.0-alpha.2. Not a released application. The hosted native GUI gate has not yet passed.**

A narrow note-clip bridge between LMMS XPT and standard MIDI. The goal is moving a musical phrase into an existing instrument clip without replacing its instrument or changing project tempo. LMMS already supports whole-project MIDI import/export; this study tests whether a smaller, clearly reviewed clip workflow is useful and technically reliable.

## Acceptance gate

The `Native XPT feasibility (experimental)` workflow must:

1. Download the official, SHA-256-pinned LMMS alpha.2 AppImage
2. Open an original project fixture with a chord, rests, an adjacent same-pitch retrigger and different note volumes
3. Use the official Piano Roll **Export clip** dialog to write `native-export.xpt`
4. Convert that actual export to MIDI and then to a generated XPT
5. Use the official **Import clip** dialog to load the generated file into an existing empty instrument clip, at a nonzero timeline position
6. Save the resulting project, load a different project, reopen the result with its native window title checked, and save a separate reopened copy
7. Independently compare native XML against literal expected notes; compare the destination instrument's entire saved subtree, tempo, track settings, and clip position
8. Decode MIDI with Mido against hand-written note/tick expectations; render diagnostic MIDI using distro FluidSynth and check known pitches/onset intervals with missing-note and shifted-note negative controls

Embedding a generated clip into a project file is **not** an alternative way to pass this gate. The only script that creates a project fixture runs before LMMS opens it. Only the native GUI may write the post-import project and native XPT export. The independent oracle imports no converter code.

## Current scope

- Exactly LMMS **1.3.0-alpha.2**, file version 31; stable 1.2.2 is outside scope
- Uncompressed XPT; standard MIDI formats 0 and 1 with one note-bearing track and one channel
- Normal notes, chords, rests, adjacent same-pitch retriggers; LMMS has 48 ticks per quarter note
- End-of-track time preserves trailing clip length, including trailing rests
- MIDI tempo is audition metadata; it is never applied to an LMMS project
- MIDI output uses 120 BPM for audition only

### Explicit losses and rejections

LMMS volume 0–200 and MIDI velocity 0–127 are different scales. Conversion uses nearest rounding with ties upward. It is **not lossless**. For example, LMMS volume 100 becomes MIDI velocity 64, then LMMS volume 101. Every mapped value is listed in a review report. Zero-volume notes are rejected because MIDI zero-velocity note-on means note-off.

Nonintegral 48-PPQN timestamps are rejected by default. An explicit nearest-tick quantization flag is needed; the report contains exact rational timestamps and signed rounding errors. Collapsed or overlapping notes after quantization remain errors. Clip name/color and source song position are not represented in MIDI. Their source values and the return defaults (including fixed-length autoresize=0 and 16-step editor context) are disclosed in the report. Other step-context values are rejected.

Rejected: step notes/clips, per-note panning, detune/automation, controllers, program changes, pressure, pitch bend, SysEx, SMPTE timing, multiple note channels/tracks, same-pitch overlap, tempo changes, unsupported metadata/fields, nonzero release velocity, trimmed clips, malformed files, non-UTF-8/DTD/entity/PI/text-bearing XML, and oversized inputs. XPTZ and project-file editing are outside scope.

**No audio-equivalence promise.** FluidSynth validates MIDI playback evidence only. It cannot prove that LMMS instruments, effects or automation sound identical.

## Local source checks

Python 3.12 standard library is enough for the prototype and unit tests:

```sh
python -m unittest discover -s tests -v
python -m pattern_ferry phrase.xpt phrase.mid --report export-review.json --accept-velocity-scaling
python -m pattern_ferry phrase.mid phrase.xpt --report import-review.json --accept-velocity-scaling
```

First add `--preview` to write only the proposed value/error report, without creating a conversion output. For nonintegral timing the preview includes exact quantization errors. Then use a new report filename with `--accept-velocity-scaling` and, only if needed and reviewed, `--quantize-nearest-tick` to produce the output. Outputs and reports refuse to overwrite existing files. This is a feasibility CLI, not a finished user interface. Native GUI and rendering checks run only on the hosted standard Ubuntu runner; local unit success does not establish native interoperability.

## Evidence and distribution

The hosted workflow uploads screenshots, accessibility trees, native-exported XPT, generated MIDI/XPT, native before/after projects, independent oracle reports, and rendering evidence. Failed native UI operations leave evidence and fail the job; they never silently skip or switch to project-file injection.

This repository is source-only. It includes no LMMS binaries, SoundFont, proprietary files, copied LMMS implementation, or original-code license grant. The official release and distro packages are fetched at test time for testing, not redistributed. Third-party materials retain their own licenses. See [primary sources](docs/SOURCES.md) and [test design](docs/TEST-DESIGN.md).
