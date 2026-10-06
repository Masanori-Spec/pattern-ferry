# Native feasibility verification

## Result

**Passed, experimental LMMS 1.3.0-alpha.2 only.**

- Verified code commit: `4e988e514a6fb2d54894f950cba8673009ef93c1`
- [GitHub Actions run 37427268358](https://github.com/Masanori-Spec/pattern-ferry/actions/runs/37427268358), completed successfully on 2026-10-06
- [Native evidence artifact 11395845057](https://github.com/Masanori-Spec/pattern-ferry/actions/runs/37427268358/artifacts/11395845057)
- Downloaded evidence ZIP: 1,610,460 bytes; SHA-256 `14fb16b1588465ca87f51bd61b02bd37964777d632d205f4db3b9889ce6b00e5`
- Evidence was downloaded, its digest checked, and actual screenshots, native XML, MIDI bytes and audio inspected independently of the converter

The GitHub artifact has a 14-day retention period. The source documentation keeps this run/commit and digest record; a private evidence backup is retained separately.

## Native route actually exercised

1. Official release AppImage passed its pinned SHA-256 check
2. The original SOURCE clip opened in the official piano roll
3. The native Export clip dialog wrote `native-export.xpt`
4. The production Python prototype converted that actual file to MIDI, then generated `generated.xpt`
5. The native Open clip dialog imported that actual generated XPT into the existing empty TARGET instrument clip
6. The application saved the result, opened a different project, reopened the result, and saved a separate reopened copy

The screenshot sequence includes an empty TARGET piano roll, the native Open clip file chooser, the generated-file import-success message, and the reopened destination clip at bar 2. The destination remained at **137 BPM**, with the **entire instrument subtree**, **track settings**, and **tick-192 timeline position** preserved. The six notes match the literal expected positions, lengths and reviewed velocity mapping. The source chord, rests and adjacent same-pitch retrigger survive.

The post-import and reopened project files are **byte-identical**. No generated XPT was embedded into a project file as a substitute for GUI import.

## Independent checks

- All 25 local/hosted unit tests passed
- Mido decoded six literal expected note/tick/velocity tuples and end-of-track at tick 384
- A separate review independently parsed the MIDI binary and checked the same literal expectations
- Native XML checks compared the fixture and full destination instrument/track state, including element text
- Deliberately missing and shifted XML notes were detected
- FluidSynth 2.3.4 rendered converter-produced diagnostic MIDI using the official Ubuntu TimGM6mb package
- Measured fundamental peaks: **440.085 Hz**, **524.199 Hz**, **660.127 Hz**, for MIDI keys 69, 72, 76
- Measured onset intervals: **0.9878 s** and **1.0027 s**, within the declared 0.03-second tolerance around one second
- Separately rendered missing-note and shifted-note controls both failed the expected second-note window check
- A separate review independently recomputed the WAV energy/pitch checks

## Native file hashes

| File | SHA-256 |
| --- | --- |
| native-export.xpt | `d2909ebdd27e039abd3ca34baf393ce6d35028c154cb4112e99d69ace1cbc274` |
| converted.mid | `b7cabff9d924006c2507f252d0268679faf7526d2371557e1e0aab99a9160327` |
| generated.xpt | `7eec93e251e0d4fc8584679b1ee8fc5ad1a68818b0efafea88b57b8082762572` |
| target-before.mmp | `275f905d8c10103e31e37eaedfb65535009fcb00a12777779d8d8b0bc9f2ef7d` |
| target-after.mmp | `b7c666d11f9c2af3c3a185c0dda82ad7e5e6b3936caf2a22fa22070b8b90b39e` |
| target-reopened.mmp | `b7c666d11f9c2af3c3a185c0dda82ad7e5e6b3936caf2a22fa22070b8b90b39e` |

## Limits

This proves the documented source-only Python prototype's note exchange path for the pinned experimental release. It does not prove stable 1.2.2 support, broader MIDI feature support, lossless velocity conversion, a finished product UI, or LMMS instrument audio equivalence. Nonintegral timing still needs explicit quantization review. Every rejected-feature boundary in the README remains in force.

A future UI or replacement converter must pass the same native test using its actual exported files. This successful Python prototype test must not be used as a substitute for testing that different producer.

## Subsequent browser result

The separate offline browser producer has now passed the same native route on its own actual UI downloads, with an additional explicit-quantization case. Its exact run, hashes and evidence are recorded in [BROWSER-VERIFICATION.md](BROWSER-VERIFICATION.md). This original Python record remains unchanged as historical proof.
