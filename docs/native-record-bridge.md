# Opt-in native-record bridge

This is a small integration example, not a fifth protocol or an execution engine.
It leaves the existing DI v0.1 reduced-envelope contract unchanged.

The check consumes four **full original records** (DIF ConfirmedIntent, DI
FeasibilityCheck, DRP decision and TIP reviewed transition), their content
SHA256 values, and the DI envelope projected from them. Missing originals are
not replaced with summaries. All shipped records, including their confirmation
and evidence assertions, are **synthetic test data**, not external observations.

## Pinned draft compatibility

| Repository | Checked revision | State when introduced |
| --- | --- | --- |
| DI | `2ef24ffcca201d3957e975d3624eec11a59bfa86` | PR #27, unmerged |
| DIF | `3d1c4df525d894c67eae5b9355b2dc0c77075673` | PR #43, unmerged |
| DRP | `92e63d7d4eeb55f8eb61956da002dc8951bab1c6` | existing main |
| TIP | `d21c57a5ccff0af569b24db0097522ee1e834388` | PR #8, unmerged |

`integrations/native_records/compatibility.json` records the revisions and every
repository source/schema file loaded, including DRP's VERSION file. External
checkouts must have the exact pinned HEAD. Working file bytes must match the
pinned Git objects before code is compiled. The report includes SHA256 for those
bytes. DI's own consumed files are pinned rather than its whole HEAD, allowing
this integration to be added without a circular dependency. An intentional
native implementation change requires compatibility review and a lock update.

The lock, code, Git object store, Python environment and checkout paths are
trusted developer inputs. This is not protection against a compromised machine
or malicious replacement of both a lock and its implementation. No module path,
command or dependency URL comes from the untrusted record bundle. The validator
performs no network access and does not dereference evidence strings.

## What actually runs

DIF uses its original Draft 2020-12 schema with a real date-time format checker.
There is no claim that the separate human-response validators authenticate this
ConfirmedIntent. DI uses its native schema-subset validator for the feasibility
record and its schema plus semantic checks for the envelope. DRP invokes its
actual reference validator, including graph rules. TIP invokes its actual
schema-subset and semantic-invariant functions. These are not reimplementations
of the native validators inside the integration.

Reports keep native validity, envelope validity, body binding and mapping as
separate axes. Unreached axes remain NOT_RUN; errors in dependencies are ERROR,
not negative-test success. CLI exit codes: 0 PASS, 1 invalid input/consistency,
2 infrastructure or unreadable input. Schema-only checks do not prove that an
assessment is factually correct.

## Deliberately narrow mapping

Only a reviewed, read-only example with unconditional `allowed` action entries
is supported. `allowed_with_constraints` and `requires_human_review` are not
promoted to allowed. The chosen DRP decision must be an evaluated, unblocked DI
action and exactly match DI's recommended step and TIP's action summary.

DRP `complete` does **not** automatically mean envelope `committed`. The native
DRP record must also contain explicit `metadata.native_bridge` assertions:
`commitment_recorded: true`, `mode: read-only-example`, and exact intent,
feasibility, transition and envelope references. These are integration-local
metadata, not a new DRP lifecycle status or proof of execution permission.

DIF's statement, DI's request and DRP's context must match literally. All
projected fields are recomputed from the originals and compared with the
submitted envelope. This is exact field equality, not NLP-based equivalence or
proof that a decision preserves every nuance of human intent.

Native TIP `reviewed` alone is insufficient for this bridge. Nonblank evidence
references and an observed next state are required; no evidence is fabricated
from review prose. The transition's source must match its stated initial state
and its target must match the reviewed next state.

## Digest profile and limits

Record digests are SHA256 over Python `json.dumps(record, sort_keys=True,
ensure_ascii=False, separators=(",", ":"), allow_nan=False)` encoded as UTF-8.
This is **not RFC8785/JCS** and is not a portable numeric canonicalization promise.
Digests bind this decoded-record representation, not whitespace in the original
JSON file. Strict parsing rejects duplicate keys, NaN, infinity and float
overflow; input files are bounded to 512 KiB.

Changing an original record without its digest fails binding. Changing both a
mapped field and its digest while leaving the projection stale fails mapping.
An actor who changes every record and digest consistently can still produce a
self-consistent bundle: authenticity, external completeness, real human consent,
execution authority and actual payment effects are **not evaluated**. Temporal
truth and authenticity of remote evidence are also outside this example.

## Reproduce

Use a checkout containing this bridge and PR #27's code. Create a disposable
virtual environment, then install only the integration requirements:

```sh
python -m venv .venv-native
. .venv-native/bin/activate
python -m pip install -r integrations/native_records/requirements.txt
```

The following one-time setup uses fresh directories and downloads only public
source code. The validator itself stays offline. Do not run it on existing
`.native` directories you need to preserve.

```sh
mkdir -p .native
for repo in DIF DRP transition-intelligence-protocol; do
  name="$repo"
  case "$repo" in transition-intelligence-protocol) name=TIP;; esac
  git clone "https://github.com/safal207/$repo.git" ".native/$name"
done
```

In these disposable dependency clones, check out the exact revisions (not
moving branch heads):

```sh
git -C .native/DIF checkout --detach 3d1c4df525d894c67eae5b9355b2dc0c77075673
git -C .native/DRP checkout --detach 92e63d7d4eeb55f8eb61956da002dc8951bab1c6
git -C .native/TIP checkout --detach d21c57a5ccff0af569b24db0097522ee1e834388
```

Then run:

```sh
python -m unittest discover -s integrations/native_records -p 'test_*.py' -v
python integrations/native_records/bridge.py integrations/native_records/example.json
```

The dedicated workflow performs those exact-revision checkouts on Python 3.11
and 3.12, runs the integration regressions and the prior DI harness tests, and
uploads the native report. Test mutations cover body/projection drift, original
record absence, native schema and graph failures, unsupported mappings, evidence
requirements, invalid numbers, dependency corruption and infrastructure errors.
