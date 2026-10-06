# PatternFerry: offline note-clip exchange

**Experimental LMMS 1.3.0-alpha.2 only. The packaged Japanese/English offline app passed its browser → official LMMS GUI import/save/reopen gate on October 6, 2026, including explicitly reviewed quantization.**

[Offline ZIP](pattern-ferry-offline.zip) · [Verified browser/native run](https://github.com/Masanori-Spec/pattern-ferry/actions/runs/37436784556) · [Evidence and exact scope](docs/BROWSER-VERIFICATION.md)

A dependency-free Japanese/English offline note-clip bridge between LMMS XPT and standard MIDI. Extract `pattern-ferry-offline.zip` and open `index.html` directly; no server, account, upload or network access is needed.

The browser preview lists every note's exact converted start/end, signed timing error, source/destination velocity and signed velocity-rounding error. Nonintegral timing is blocked by default. Selecting nearest-tick rounding resets acknowledgment. Export requires a fresh explicit acknowledgment of all displayed changes. JSON and print reports retain the review evidence.

The original Python converter remains an independent comparison implementation. The JavaScript implementation has its own bounded XML/MIDI parser, with no shared conversion code or runtime dependencies.

The goal is moving a musical phrase into an existing instrument clip without replacing its instrument or changing project tempo. LMMS already supports whole-project MIDI import/export; this study tests whether a smaller, clearly reviewed clip workflow is useful and technically reliable.

## Acceptance gate

The `Browser and native XPT gate (experimental)` workflow requires all of the following. The browser producer passed at `d81b0e2c46d251487194e32b8c77841ee4032b1b` using actual UI downloads. The earlier independent Python proof is preserved [separately](docs/VERIFICATION.md):

1. Download the official, SHA-256-pinned LMMS alpha.2 AppImage
2. Open an original project fixture with a chord, rests, an adjacent same-pitch retrigger and different note volumes
3. Use the official Piano Roll **Export clip** dialog to write `native-export.xpt`
4. Load that actual export in the offline browser UI, acknowledge the full review, and save actual browser MIDI/XPT downloads; independently compare them with Python
5. Use the official **Import clip** dialog to load the generated file into an existing empty instrument clip, at a nonzero timeline position
6. Save the resulting project, load a different project, reopen the result with its native window title checked, and save a separate reopened copy
7. Independently compare native XML against literal expected notes; compare the destination instrument's entire saved subtree, tempo, track settings, and clip position
8. Decode browser MIDI with Mido against hand-written note/tick expectations; render browser-downloaded diagnostic MIDI using distro FluidSynth and check known pitches/onset intervals with missing-note and shifted-note negative controls
9. Natively import/save/reopen a separately acknowledged browser-quantized XPT against literal timing and velocity expectations
10. Check Japanese/English desktop/mobile, keyboard access, offline file use, stale asynchronous loads, repeated/empty input changes, rejection/size boundaries and print output

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

Rejected: step notes/clips, per-note panning, detune/automation, controllers, program changes, pressure, pitch bend, SysEx, SMPTE timing, multiple note channels/tracks, same-pitch overlap, tempo changes, unsupported metadata/fields, nonzero release velocity, trimmed clips, malformed files, non-UTF-8 XML, external/internal DTD subsets, entities, processing instructions, text-bearing XML, and oversized inputs. XPTZ and project-file editing are outside scope.

**No audio-equivalence promise.** FluidSynth validates MIDI playback evidence only. It cannot prove that LMMS instruments, effects or automation sound identical.

## Local source checks

Python 3.12 and Node.js run the independent unit suites without installing browser binaries:

```sh
python -m unittest discover -s tests -v
node --test tests/test_browser_core.cjs
python scripts/build_offline.py
python -m pattern_ferry phrase.xpt phrase.mid --report export-review.json --accept-velocity-scaling
python -m pattern_ferry phrase.mid phrase.xpt --report import-review.json --accept-velocity-scaling
```

First add `--preview` to write only the proposed value/error report, without creating a conversion output. For nonintegral timing the preview includes exact quantization errors. Then use a new report filename with `--accept-velocity-scaling` and, only if needed and reviewed, `--quantize-nearest-tick` to produce the output. Outputs and reports refuse to overwrite existing files. The CLI remains available independently of the new browser interface. Native GUI and rendering checks run only on the hosted standard Ubuntu runner; local unit success does not establish native interoperability.

## Evidence and distribution

The hosted workflow uploads screenshots, accessibility trees, native-exported XPT, generated MIDI/XPT, native before/after projects, independent oracle reports, and rendering evidence. Failed native UI operations leave evidence and fail the job; they never silently skip or switch to project-file injection.

This repository is source-only. It includes no LMMS binaries, SoundFont, proprietary files, copied LMMS implementation, or original-code license grant. The official release and distro packages are fetched at test time for testing, not redistributed. Third-party materials retain their own licenses. See [primary sources](docs/SOURCES.md) and [test design](docs/TEST-DESIGN.md).

## Browser verification status

- Passed locally: 25 independent Python tests, 62 JavaScript tests, syntax checks, deterministic offline package validation, and the native fixture's byte-exact JS/Python MIDI comparison
- Passed in the exact-commit hosted run: 18 real-browser scenarios, actual browser-download official LMMS GUI import/save/reopen (normal and quantized), independent Mido/XML/Python checks, and FluidSynth positive/missing/shifted-note controls
- Independently inspected: downloaded artifact digest, native XML/MIDI/audio, Japanese/English desktop/mobile screenshots, sandboxed browser command lines, and the two-page print report
- Browser test dependency: pinned Playwright 1.63.0, development/CI only; no third-party JavaScript, browser binary, font or SoundFont is bundled in the offline ZIP
- See [browser acceptance design](docs/BROWSER-ACCEPTANCE.md)
