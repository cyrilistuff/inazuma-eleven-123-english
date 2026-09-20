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
