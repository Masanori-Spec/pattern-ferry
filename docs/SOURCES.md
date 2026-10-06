# Primary sources and pin

Checked 2026-10-06. These references explain the format and native commands; they are not evidence that our GUI test has passed.

- [Official LMMS alpha.2 release](https://github.com/LMMS/lmms/releases/tag/v1.3.0-alpha.2): pre-release, published September 6, 2026. The release warns that it is less stable than stable releases and that saving projects is a one-way upgrade from older versions. This prototype must not be presented as stable 1.2.2 support.
- [Release API](https://api.github.com/repos/LMMS/lmms/releases/tags/v1.3.0-alpha.2): Linux x86-64 AppImage asset ID 546488552, 154,339,832 bytes, SHA-256 `7580e832b9a10041ef632ebf2d70d588f41c31be8c6c80d1f9a96d1c0871298b`
- [PianoRoll.cpp, alpha.2](https://github.com/LMMS/lmms/blob/v1.3.0-alpha.2/src/gui/editors/PianoRoll.cpp): file-action menu and export/import dialogs. Import loads clip settings and restores the existing timeline position
- [MidiClip.cpp, alpha.2](https://github.com/LMMS/lmms/blob/v1.3.0-alpha.2/src/tracks/MidiClip.cpp): clip fields, normal note storage, offset and length behavior
- [Note.cpp, alpha.2](https://github.com/LMMS/lmms/blob/v1.3.0-alpha.2/src/core/Note.cpp): note attributes and detuning child data
- [DataFile.cpp, alpha.2](https://github.com/LMMS/lmms/blob/v1.3.0-alpha.2/src/core/DataFile.cpp): standalone midiclip envelope; 31 upgrade methods establish current file version 31
- [MidiExport.cpp, alpha.2](https://github.com/LMMS/lmms/blob/v1.3.0-alpha.2/plugins/MidiExport/MidiExport.cpp): direct pitch keys, 48-PPQN interpretation and 200-to-127 scale
- [Note.h, alpha.2](https://github.com/LMMS/lmms/blob/v1.3.0-alpha.2/include/Note.h): 128-key range
- [Mido documentation](https://mido.readthedocs.io/en/stable/files/midi.html): independent MIDI decoder used by the hosted oracle
- [FluidSynth command line](https://www.fluidsynth.org/api/fluidsynth_cli.html): independent MIDI renderer; the workflow installs Ubuntu packages instead of bundling vendor binaries

Code here was written for the narrow interchange behavior; LMMS source is consulted to understand the file format and GUI, not copied into the distribution.
