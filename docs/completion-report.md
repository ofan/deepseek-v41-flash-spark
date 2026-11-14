# Public recipe upgrade — 2026-11-13

## Verdict: documentation, source and measured decode battery complete

The repository and separate runtime package are **public**, verified without owner
credentials. This unit did not change visibility, deploy an image, alter serving
settings or operate a pull request. It issued bounded decode requests and read-only
GPU/container/vector-hash inspections. Production remained on its existing vision build.

## Performance measured in this unit

Four GB10 GPUs, TP4, **2,200 MHz configured graphics-clock cap on every rank**;
power limit reported **N/A**. Live image version `2026.11.08-native-vision-trial-r1`.
All four running ranks use the authentic GLP-39 hash with no alpha/layer overrides;
the file supplies alpha0.75 and layers1–39. Clock/vector and restart/OOM proof is in
[the generic four-rank receipt](benchmarks/2026-11-13-gpu-cap.json).

| Streams | Prose decode tok/s | Code decode tok/s | Prose end-to-end tok/s | Code end-to-end tok/s |
|---:|---:|---:|---:|---:|
| 1 | 72.297 | 73.187 | 68.530 | 69.160 |
| 4 | 107.232 | 161.501 | 105.263 | 156.611 |
| 8 | 156.079 | 261.548 | 58.594 | 259.196 |
| 16 | 236.405 | 320.541 | 234.320 | 252.712 |

**58/58 successful requests**,256 output tokens each; zero request errors. Existing
built-in prose/code prompts and original multi-stream measurement functions, no new
eval prompts. One wave per cell, shared production, repeated same-arm input; not a
sustained or statistically repeated capacity test. Decode excludes first-token delay.
Eight-stream prose TTFT was21.882–23.619s and16-stream code TTFT3.478–4.446s; no cause
is attributed. [Complete method and per-request timing](benchmarks.md#fresh-decode-battery-2026-11-13).

Accepted-production prefill is retained unchanged: **8,951 /9,259 /9,076 /8,598 tok/s**
at32K/131K/near500K/near1M. The vision check is88/88 correct off and88/88 on across six
fixtures and their repeat/streaming/concurrency combinations. Stock fidelity is9/9
bit-identical off and9/9alpha-zero including the1M-token needle. These historical
production checks are attributed in [benchmarks](benchmarks.md), not represented as
fresh model acceptance of the sanitized public runtime.

## Included implementation and build path

- `vendor/engine/`: **265 files** from the production implementation at **b7c3eb5**,
  including engine, frontend, vision tools, existing prose/code benchmarks, notices
  and a generic fleet template needed by CMake.
- `vendor/upstream/`: **246 files** from the corresponding Pico base **4e70b2ab**.
- **46 production files generalized** for privacy: deployment paths, addresses,
  local reference names and fleet configuration; per-file original/sanitized hashes
  and categories are retained. Source is deliberately not claimed byte-identical
  after these disclosed substitutions. Engine arithmetic/protocol literals are retained.
- `patches/`: four separate feature patches—GLP steering, DSML parser hardening,
  sampler clamp, native vision—plus one separate production cache-fidelity prerequisite.
  This is an ordered five-patch series, not four independent pristine-base diffs.
  Replay matches all265 final files and executable modes exactly.
- Source staging, native compilation, lossless conversion, compact vision extraction
  and optional cross-build now consume **in-repository artifacts**, not external fork
  checkouts. The source-build receipt binds actual local binary hashes to the included
  source manifest and labels the assembled result unqualified.
- README/setup cover requirements, model preparation, public image pull, completed
  user-specific fleet config, per-rank launch, health/text/image requests and troubleshooting.
  Steering now defaults ON: GLP-39, alpha 0.75, layers 1–39; explicit
  `--steering off` opts out on every rank. Quick-start passes `--steering glp39`
  explicitly because the immutable published image retains its older embedded
  launcher. No private mirror acquisition is required or instructed.

## Public access readback

Public artifact:

```text
ghcr.io/ofan/deepseek-v41-flash-spark-public:2026.11.11-native-vision-sanitized-candidate-r4
sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979
```

Anonymous registry pull-token exchange200, manifest GET200 and raw-manifest SHA256
match; repository page200 and HTTPS clone exit0 with an empty temporary home, no
credential helper or owner credentials. [Readback receipt](public-readback-20261113.json).
The protected predecessor's anonymous pull-token request still returns401; it is
not a distribution input and was not modified. No new package or visibility action
occurred here. Historical copy/audit receipts remain dated provenance; the current
state is in `public-release.json`.

## Verification and limits

- **106/106 recipe tests**, including source-tamper/mode rejection, staging, exact
  patch replay, source-build receipt validation, the then-current OFF default, benchmark
  provenance and disclosure-detector regressions.
- **38/38 Rust frontend tests** (`cargo test --locked --lib -j2`).
- Host GLP reader test passes with the authentic vector; arithmetic comparison has
  **0 fixed/reference differences** across798,720 fold values/156dot rows. Sampler
  host test passes its16,777,216-bin exhaustive check. GLP host compilation used a
  temporary type-only `cudaStream_t` declaration, not a CUDA runtime or GPU test.
- Python AST, JSON and shell syntax checks pass across included source. Working-tree
  and reachable-history scrub: **zero forbidden disclosures**. Actual parser literals
  necessarily remain in parser/test/patch source; the narrowly scoped protocol-literal
  allowance does not exempt operator, network or credential findings.
- Patch replay and source hashes/modes pass. Text/vision planning commands pass
  without downloading weights or executing conversion. Whitespace checks pass.

[Machine-readable verification](recipe-verification.json). Final commit/push IDs
are reported in the turn result; the resulting reachable history is rechecked before push.

## Residual qualification / reproduction gaps

1. The public image remains a **sanitized twin with GPU serving qualification pending**:
   same source, byte-identical frontend/vision assets, generic-path rebuilt engine and
   new runtime/launcher. The previous incomplete import smoke is a qualification note,
   not a claim of a passed runtime test. No full-ring GPU qualification occurred here.
2. Public-source checkpoint acquisition, full lossless text conversion, compact extraction
   and all-in-one image assembly have not been executed end to end in this unit.
   These remain explicit build-host tasks; the public runtime intentionally lacks text assets.
3. The exact original cross-toolchain/sysroot is not distributed. Native ARM64 commands
   and source provenance are supplied; independent byte-identical binaries are not promised.

The repository's MIT notices credit Andy Shu and Picom, DeepSeek and msuiche;
dependencies keep their own terms. This is an unofficial recipe, not a vendor endorsement.
