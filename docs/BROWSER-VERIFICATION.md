# Offline browser verification

## Result and identity

**Passed for the documented note-only subset of experimental LMMS 1.3.0-alpha.2.** This is the browser producer's own native result, not a reuse of the earlier Python feasibility proof.

- Tested code: `d81b0e2c46d251487194e32b8c77841ee4032b1b`
- [Successful run 37436784556](https://github.com/Masanori-Spec/pattern-ferry/actions/runs/37436784556), 2026-10-06
- [Evidence artifact 11399364098](https://github.com/Masanori-Spec/pattern-ferry/actions/runs/37436784556/artifacts/11399364098)
- Downloaded artifact: 4,372,951 bytes; SHA-256 `07d7f1aa7f38cdd3415599b60d950c32c86edb2404ead144246384eea5170a78`
- Tested offline ZIP: SHA-256 `7a35beb521a0b020f3a3211d33e317cb6d50f4f34a15788de6402e54aa42d199`

The exact five-file source-only ZIP was verified and extracted before the browser opened its `index.html` using the file protocol with networking disabled. It contains no LMMS, browser or SoundFont binaries. GitHub evidence expires after 14 days; an exact private evidence backup is retained separately.

## Actual native route

The pinned official AppImage exported a newly opened original six-note SOURCE clip through Piano Roll → File actions → Export clip. The browser selected that actual file, displayed the review, required acknowledgment and downloaded MIDI. It then selected that MIDI and downloaded XPT through the same visible UI. The harness never called the JavaScript converter API to obtain production output.

The official Import clip dialog loaded the downloaded XPT into an existing empty TARGET instrument clip. LMMS saved the result, opened a different project, reopened the result with its active project title checked, and saved a second copy. Both saved projects were byte-identical. Literal note expectations, **137 BPM**, the **entire instrument subtree**, track settings and **tick-192 destination position** passed independent checks. No XPT was embedded into an MMP as a substitute for native import.

The six-note chord/rest/retrigger fixture returned LMMS volumes 200, 101, 50, 76, 124 and 150, matching the explicitly disclosed lossy MIDI mapping. The end-of-track remained tick 384.

## Explicit quantization case

A hand-written 100-PPQN MIDI note started at tick 1 and ended at tick 25, key 60, velocity 100. Exact mode blocked export. The browser's nearest-tick option and acknowledgment produced a one-note XPT, which also passed actual native import/save/different-project/reopen/save.

- Exact start: `12/25` of a 48-PPQN tick → output `0`; error `-12/25`
- End: `12` → `12`; error `0`; output note length `12`
- Velocity: `100` MIDI → `157` LMMS; ideal `20000/127`; error `-61/127`
- The JSON report recorded `rounding: nearest` and `acknowledged: true`
- Destination tempo, instrument and position stayed unchanged; quantized saved/reopened projects were byte-identical

## Independent and visual checks

- 25 Python tests and 62 JavaScript tests passed
- Original Python comparison: byte-identical MIDI and semantically identical normal/quantized XPT; no shared conversion implementation
- Mido: six hand-written note/tick/velocity tuples and end-of-track; direct native XML checks and deliberate missing/shifted-note negatives
- FluidSynth 2.2.5 rendered actual browser-downloaded diagnostic MIDI through the official Ubuntu TimGM6mb package
- Positive fundamental peaks: 440.085, 524.199 and 660.127 Hz; onset intervals 0.9878 and 1.0027 seconds (one-second target, ±0.03-second tolerance)
- Separately rendered missing-note and shifted-note controls both failed the expected second-note window
- 18 actual browser scenarios passed: JA/EN desktop and 390px mobile, keyboard, repeated/empty input changes, asynchronous stale results/Clear, size and unsupported-input rejection, exact/rounded review, print and file-protocol offline use
- Browser console errors and HTTP(S) requests: none
- Recorded Chromium launch commands kept the sandbox enabled, with neither `--no-sandbox` nor `--disable-setuid-sandbox`
- Actual desktop/mobile screenshots and the two-page print PDF were inspected; the context JSON stays together and all six note/error rows remain legible

The downloaded artifact's digest, real native screenshots, saved XML, MIDI bytes, quantization report and rendered audio were independently reviewed in addition to CI assertions.

## Selected output hashes

| File | SHA-256 |
| --- | --- |
| converted.mid | `b7cabff9d924006c2507f252d0268679faf7526d2371557e1e0aab99a9160327` |
| generated.xpt | `cd6745272704ee03266bfde061c65d78091a95e9ded461cd35cacc1da46eb06a` |
| target-after.mmp / target-reopened.mmp | `ddf77d4635f7a105fb7b8fee26170ca179c30b965cf36834b51224828983c3d0` |
| quantized.xpt | `369ed4a97c7d8671ecad7b96346ef7cf6b9feb725aa304968127edb68ce6b523` |
| target-quantized.mmp / target-quantized-reopened.mmp | `56ff22ef626f54477c949094d8060a340ea0902db05c210ef1c7079abbd9dde6` |

## Limits

This is an experimental, bounded offline utility, not stable LMMS 1.2.2 support or a general MIDI importer. Velocity scaling remains lossy, nonintegral timing needs explicit review, and all documented unsupported-field rejections remain. The audio evidence validates diagnostic MIDI playback only; it does not establish LMMS instrument/audio equivalence. Desktop Chrome/Chromium was exercised; other browser engines and operating systems are not certified by this run. Delivery is GitHub source plus the offline ZIP, with no hosted-service requirement or original-code license grant.
