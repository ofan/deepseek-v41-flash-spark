# Production implementation changes

Upstream base: Pico commit **4e70b2ab**. Target: production source **b7c3eb5**.
Both implementation snapshots are included in this repository; no external fork
checkout is needed. Apply the files listed in `series`, in order, to a copy of
`vendor/upstream/`. The result is checked byte-for-byte against `vendor/engine/`
(excluding the two snapshots' provenance manifests).

Four feature changes have their own standalone consolidated patch files:

| File | Change |
|---|---|
| `0002-glp-steering.patch` | Runtime spec-v1 steering, including the reference fold arithmetic correction |
| `0003-dsml-parser.patch` | Streamed tool-call framing, quoted values and quarantined-output raw capture |
| `0004-sampler-clamp.patch` | Keep uniform sampler noise strictly below one |
| `0005-native-vision.patch` | Native tower/frontend/span injection, bounds and production stop-token count |

**Do not omit `0001-cache-fidelity-prerequisite.patch`.** Production also includes
three retained-session/prompt-checkpoint repairs. They are separate from the four
features and are needed to reproduce production and its stock-fidelity controls.
Hiding them in a feature patch would be misleading. This is a five-file patch series
on the upstream base, not a claim that the four feature patches independently apply
without their predecessors. `manifest.json` maps every patch to source commits/files.

Only deployment paths/defaults/documentation addresses were generalized in both
snapshots and patches; exact original/sanitized file hashes and per-file categories
are in the source manifests and `vendor/sanitization.json`. Original protocol literals
are retained because parser/tokenizer correctness depends on them. Operator/secret
scrubbing applies to all source and patches; protocol literals are not disclosures.

Check/replay locally without contacting upstream:

```sh
python3 scripts/verify-patches.py
```

No patch is applied to a production system by these scripts. MIT licenses and
upstream notices are preserved in each snapshot.

Unified-diff context includes literal space-only lines. `.gitattributes` disables
whitespace rewriting for patch files; content hashes and exact replay remain enforced.
