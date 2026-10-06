# Browser producer acceptance

The original Python native proof is preserved in VERIFICATION.md. It does not establish the new browser producer's correctness. Until a fresh exact-commit hosted run and independent artifact review pass, this is an experimental UI candidate.

## Actual outputs, not a simulated producer

The native harness first uses the official LMMS GUI to export a fresh original fixture. `browser_convert.mjs` verifies the exact shipped offline ZIP, materializes its five source files and opens that packaged UI with networking disabled, selects that native file through the actual file input, acknowledges the displayed review and captures actual browser downloads. It never calls the production converter's JavaScript API. Those exact downloaded MIDI and XPT files feed Mido and the official LMMS import dialog.

The original independent Python converter checks browser MIDI byte equality and browser XPT semantic equality. The native XML/Mido oracles still use literal expected notes rather than either converter's output as the reference.

The same browser download path creates the positive, missing-note and shifted-note MIDI rendered by FluidSynth. A separately reviewed fractional-timing MIDI produces `quantized.xpt`; the native application imports it, saves, opens another project, reopens it and saves a second copy. Its literal expectation is one key-60 note at tick 0, length 12, volume 157, with the destination still at 137 BPM and tick 192. The report must show start error -12/25 tick and velocity-rounding error -61/127, with explicit nearest-tick policy and acknowledgment.

## Review and input safety

- File size checked before browser byte reading; parser independently enforces 2 MiB
- At most 4096 notes, 16384 MIDI events, 32 tracks and XML depth 8
- Strict UTF-8 XML subset; inert native prolog DOCTYPE allowed, external/internal DTD subsets, entities other than predefined/numeric characters, PI, comments, non-whitespace text, unknown elements/attributes and malformed XML rejected
- No general XML resolver, network request, `eval` or user HTML insertion
- Same supported/rejected musical subset as the Python contract
- Preview includes every note, all source/exact/rounded timing and velocity values, signed rational errors, clip-end error and source context
- Exact mode blocks nonintegral timing; nearest mode must be explicitly chosen; zero-length/overlap after rounding remains blocked
- Every file or policy change clears acknowledgment; newer reads win and Clear cancels pending work
- Native import overwrites its chosen destination clip; the UI advises making a copy in LMMS first

## Browser evidence

Hosted checks retain Japanese and English desktop, 390px mobile, all-notes print PNG/PDF, real file downloads, JSON review, input-rejection and asynchronous-race results. The file-protocol offline UI must make no HTTP(S) requests. The offline ZIP is source-only and deterministically built; its manifest lists exact component hashes.

Release acceptance is the exact GitHub source plus the verified source-only offline ZIP. The packaged app runs from index.html without a server; its actual browser-downloaded XPT and MIDI files must pass the native and independent checks described above.

## Hosted browser sandbox

The browser runs with Playwright `chromiumSandbox:true` on the standard Ubuntu 22.04 runner. Each browser launch records the actual main-process command and rejects `--no-sandbox` or `--disable-setuid-sandbox`. No AppArmor, kernel, security or browser-sandbox setting is disabled. Ubuntu 22.04 meets the pinned official LMMS build's glibc 2.35 baseline.

A job-scoped `PLAYWRIGHT_BROWSERS_PATH` points to the same workspace cache during installation, UI checks and native conversion. Changing the synthetic LMMS HOME cannot silently select or lose a different browser executable.
