# English patch work guide

## Current state

This branch is a starting point, not a working English patch. Upstream's
`translation/ie1/dialogo.csv` has 29,985 Spanish project rows and
`translation/ie2/dialogo.csv` has 89,970. Its released patches and multimedia
are Spanish. Inazuma Eleven 3 has no translation corpus here. A full English
release needs new text, UI art, and in-game verification.

The target locale is `en-GB`, matching the European English names used in the
series. Record exceptions and sources in the English glossary as work proceeds.
The existing Spanish files are references only; do not pass them into a build
advertised as English.

## Start translating IE1

From the repository root, run:

```powershell
python tools/english_workspace.py init --game ie1
python tools/english_workspace.py status --game ie1
```

The first command creates `translation/en/ie1/dialogo.csv` using the event IDs
and Japanese keys already present upstream. It leaves `en_final` empty. Enter
English text and set `estado` to `review` or `approved`; keep literal control
codes such as `%s`, `%d`, `\\n`, and `\\f` intact. Re-running `init` merges
new upstream keys without overwriting English work. `status` reports coverage
and rejects missing control codes or divergent translations for the same key.

Do not import official dialogue dumps into Git. If comparing against your own
English game copy, keep extracted sources under ignored `work/` and commit only
reviewed translation entries. The upstream `ds_official.py` alignment is known
to mispair lines; see issue #36 in the upstream repository before adapting it.

### IE1 English DS reference

With a personal European English IE1 DS dump, the extracted `script/en/evet.pkb`
and `.pkh` can be kept in
`work/ie1/english_references/data_iz/script/en/`. Extract the Japanese 3DS
RomFS with `tools/extract_romfs.ps1`, then run:

```powershell
python tools/english_reference.py
```

This writes an ignored `work/ie1/english_references/alignment/ie1_ds_pairs.csv`
and `summary.json`. The tool matches event IDs and string IDs, accounting for
instruction shifts documented in `EVENT_SCRIPT_FORMAT.md`. It never copies
official English text into `translation/en/ie1/dialogo.csv`. `review` means a
candidate to inspect, not an approved translation; `check_event_alignment`,
`ambiguous_same_japanese`, and `placeholder_mismatch` need particular care.
The inherited DS character table was developed for Spanish and may need
checking against English punctuation. Some 3DS lines have no DS equivalent.

The first ten opening-scene lines (`92010100`) have been adapted into the IE1
English CSV with `review` status. To stage only those lines as a local SSD file:

```powershell
$env:PYTHONPATH = 'tools/src'
python -m ie123kit.ie1.texto.english_stage --event 92010100 --include-review
```

The output in `work/ie1/english_probe/` is ignored by Git. The stage command
uses the frozen dialogue wrapping and fullwidth encoder, rejects unsupported
characters and oversized records, and checks that SSD instructions are unchanged.
It is not a playable archive. A later build must still pass the approved font
hash lock and the in-game QA protocol.

### IE2 Firestorm and Blizzard

`translation/en/ie2/dialogo.csv` is an empty English workspace with 87,432
unique Japanese keys. The European DS Firestorm and Blizzard copies supplied
for local reference have byte-identical `script/en/evet.pkb` and `.pkh` files.
Unlike IE1, these IE2 `evet` files contain mostly script metadata in the format
parsed above; applying the IE1 event/string ID matcher gives almost no usable
dialogue pairs. IE2 needs its own text-source investigation before importing
English lines. The two 3DS editions also have distinct `eve.pkb` scripts, so
version-specific dialogue must be checked separately.

## Before a first candidate

- Add an English-only build path. The inherited reinserters and release
  workflow refer to Spanish paths, fields, assets, and filenames.
- Keep the five frozen typography files and `tools/dialogue_lock.py` checks
  intact. English sentences must fit the approved dialogue layout.
- Run the repository guards and toolkit tests, then follow
  [the IE1 playtest protocol](PROTOCOLO_QA_IE1.md). Static checks alone do not
  establish playability.
- Generate a patch only against a personal lawful dump of `CTR-P-AETJ`.
  Never commit a ROM, extracted asset, or local build.
