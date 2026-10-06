PatternFerry / 実験版・Experimental

ZIP を展開し、index.html をブラウザで開いてください。サーバー・アカウントは不要です。
Extract the ZIP and open index.html in a browser. No server or account is needed.

LMMS 1.3.0-alpha.2 / 形式 version 31 の通常音符だけが対象です。
Only normal-note clips from experimental LMMS 1.3.0-alpha.2, file version 31 are supported.

XPT / MIDI を選び、すべての時刻・強弱・丸め誤差を確認し、確認欄にチェックしてから書き出します。
Select XPT / MIDI, review every timing/velocity value and rounding error, then acknowledge before export.

MIDI で 48 PPQN に収まらない時刻がある場合、明示的に「最も近い tick」を選ぶ必要があります。
Nonintegral 48-PPQN times require explicit nearest-tick rounding.

LMMS 0–200 と MIDI 0–127 の強弱変換は可逆ではありません。楽器音の一致は保証しません。
Velocity scaling between LMMS 0–200 and MIDI 0–127 is lossy. No LMMS audio-equivalence promise.

LMMS でクリップを複製し、Piano Roll → File actions → Import clip から XPT を読み込んでください。
Make a copy of the destination clip in LMMS, then use Piano Roll → File actions → Import clip.
取り込み先のクリップは上書きされます。プロジェクトのテンポと楽器はそのままです。
The chosen clip is overwritten. Its project tempo and instrument remain unchanged.

ソースのみ。LMMS 本体・SoundFont・ブラウザのバイナリは含みません。
Source-only distribution; no LMMS, SoundFont or browser binaries are included.
Original-code license grant is not included. Third-party applications retain their own licenses.

Source and verification: https://github.com/Masanori-Spec/pattern-ferry
