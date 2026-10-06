# Test design and honest stopping condition

## Native GUI is the mandatory gate

The converter's own reader/writer agreeing with each other is insufficient. A project file containing generated note XML is also insufficient. The actual official application must export XPT, import a generated XPT using its UI into an existing clip, save, reopen, and expose the expected note data independently in its resulting project.

The source project is an original hand-written fixture, clearly labeled as such. Its notes are not called native XPT until LMMS has exported them. The target project is an original empty instrument-clip fixture with a different tempo (137 BPM), nondefault instrument settings, and a clip at tick 192. The native application saves a fresh normalized baseline to a new path before import. Every required native output must be absent at start, preventing stale-evidence reuse. The independent XML oracle compares all instrument state, track attributes, tempo, and destination clip position between that baseline and the native post-import save. It then loads a different project, reopens the output, checks the active native main-window filename after the dialog closes, and saves a fresh reopened copy for another independent note, instrument, track and project-header comparison.

Original source notes at 48 PPQN:

| Start | Key | Length | LMMS volume |
| ---: | ---: | ---: | ---: |
| 0 | 60 | 48 | 200 |
| 0 | 64 | 48 | 100 |
| 0 | 67 | 48 | 50 |
| 96 | 60 | 24 | 75 |
| 120 | 60 | 24 | 125 |
| 192 | 69 | 48 | 150 |

Clip duration is 384 ticks. Expected MIDI velocities are 127, 64, 32, 48, 79, 95. After return, expected LMMS volumes are 200, 101, 50, 76, 124, 150. These expectations are literal data, not derived by the converter under test.

## Hosted UI method

Use a standard GitHub-hosted Ubuntu runner, Xvfb and a normal D-Bus accessibility session. Use AT-SPI for named menus/dialogs. For LMMS's custom-painted clip label, use screenshot OCR with a unique exact label. Save every screen and accessibility tree. An ambiguous label or absent GUI affordance fails the gate. No patched LMMS, injected test plugin, hidden data mutation, root GUI process, security-setting change, or local heavy GUI installation is used.

A failed menu lookup is an automation failure, not proof that LMMS lacks the feature. It is investigated from retained evidence; acceptance never changes to XML embedding. If the official GUI path cannot be demonstrated within supported hosted tooling, this concept remains no-go and no product UI is started.

## Independent layers

1. Standard-library unit tests exercise strict parsing, rejected feature boundaries, exact notes, explicit velocity scaling, rational quantization errors, and malformed inputs. The CLI reads at most 2 MiB plus one byte, rejects aliased input/output/report paths, and creates outputs exclusively. XML is UTF-8 only with bounded nesting/elements; MIDI has an event cap
2. Mido independently decodes output MIDI against hand-written pitches, ticks, lengths, velocities and end-of-track length
3. Direct XML independently examines actual native files, and detects deliberately removed/shifted notes
4. FluidSynth renders production-converter diagnostic MIDI. RMS/FFT checks compare three known pitches (69, 72, 76) and 1-second onset intervals. Missing/shifted-note MIDI is separately rendered and must fail those same assertions

The rendered diagnostics are monophonic to keep the acoustic oracle interpretable. Chords and retriggers are covered by the native XML and Mido layers. Audio checks never assert equivalence to an LMMS instrument.

## Status before hosted execution

Only unit tests and source inspection can pass locally. Native GUI, Mido hosted oracle, and FluidSynth rendering are pending until evidence from the exact published commit exists. No pass marker is pre-populated in the repository.
