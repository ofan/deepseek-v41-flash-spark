# Recipe publication — 2026-11-12

## Verdict: HELD — separate package visibility requires owner web authentication

The recipe is prepared for outside users, but **neither the repository nor the
separate distribution package is public**. No successful anonymous readback is
claimed. The repository visibility gate remains closed because publication step1
has not passed. No visibility mutation, production access, Spark operation, route
change or pull-request operation occurred.

## Image copy and access proof

Intended public artifact:

```text
ghcr.io/ofan/deepseek-v41-flash-spark-public:2026.11.11-native-vision-sanitized-candidate-r4
sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979
```

- Separate package ID **16813664**, currently **private**.
- Exact approved manifest copied without rewriting config/layers. Owner-authenticated
  GET by tag and digest matches the expected raw-manifest SHA256. All three referenced
  blobs pass digest/size HEAD checks. GHCR mounted the config and two existing layers;
  no failed blob had to be retransferred.
- Config `sha256:97cfdaafc7d1b5e7e0cd0e1b3b7a2cf787e8948586732089c9a24a334379e1df`.
  Two layers; **4,581,714,457 compressed bytes**. This is runtime/vision/vector only,
  not the hundreds-of-GB external text assets.
- Fresh anonymous checks at **2026-11-12T06:13:39Z**: candidate manifest **401**,
  anonymous pull-token request **401**. It is **not publicly fetchable**.
- Protected original package ID **16805256** remains **private** and unchanged;
  its production-mirror manifest and anonymous pull-token requests also return **401**.
  No pull instruction for that package is published here.
- Machine-readable copy and readback evidence: [public-release.json](public-release.json).

**Exact blocker:** GitHub documents package visibility changes through the package
settings web UI. Remote browser calls timed out; the isolated local browser reached
GitHub but was signed out. The checked credential stores provide package API/registry
credentials, not an available owner web login. Those credentials successfully copy
and verify the package; that does not establish access to the visibility UI. No
undocumented visibility endpoint or shared-service restart was attempted. The local
task browser was closed gracefully.

To finish: authenticate as the owner in the separate package's settings, change
**only that package** to public, then fetch the manifest using an anonymous registry
pull token and hash the raw bytes to the digest above. Recheck the protected original
package is private/anonymous-denied. Then rerun the recipe/scrub gates before changing
repository visibility. An initial registry401 challenge alone is not proof of privacy;
the recorded anonymous token request also failed.

## Repository and usability

Repository: <https://github.com/ofan/deepseek-v41-flash-spark>, branch **main**,
currently **private**. The repository was not flipped and anonymous HTTPS cloning
was not represented as passing. That verification must run after the package gate
passes and the authorized repository flip occurs.

The README now leads with purpose, 4×GB10/TP4 hardware, a digest-pinned pull/run
example, exact external-text-asset prerequisites, optional steering OFF, benchmark
provenance and MIT credits. The fleet template follows the pinned source's documented
schema and ships placeholders, not deployment addresses. Every distribution-image
reference points only to the separate public-package destination. Historical
private-predecessor audit/transfer records are retained as provenance, not downloads.

The fork metadata and pinned source README are accessible **without credentials**
(HTTP200), so obtaining converter source does not require a private repository.
No checkpoint or tensor payload was downloaded for this preparation.

## Qualification and residual gaps

- The candidate is a **sanitized twin**, not a bit-identical production executable:
  unchanged engine source **b7c3eb5**, byte-identical frontend and vision assets, engine
  rebuilt under generic paths. **GPU serving qualification is pending.** Production
  itself runs the private exact mirror. Recorded production benchmarks are labeled
  reference results, not candidate measurements.
- Candidate audit: operator findings0, unresolved findings0; **11 vendor binary
  findings WAIVED by Ryan** on 2026-11-11 at23:58EST. Full finding/adjudication evidence
  remains in `publication-audit.json` and [remediation](publication-remediation.md).
- Incomplete PyTorch import smoke remains a **qualification note, not a publication
  blocker**. No new GPU/model tests were performed here.
- The public-source text conversion/compact extraction/full all-in-one image pipeline
  has offline checks but has not been executed end to end. Text ranks/Engram/tokenizer
  are external prerequisites, not silently bundled model weights.
- Exact independent cross-toolchain/sysroot reproduction is not published. Native
  build commands are provided, without claiming byte-identical rebuilt binaries.

## Verification

**87/87 offline tests pass**; **49 current text files** have **zero forbidden matches**.
Python AST (15 files), JSON parsing (11 files), shell syntax (6 files) and diff
whitespace checks pass. The precommit reachable-history scan covered **87 blobs /
6 commits**, zero forbidden matches; a final committed-history scan follows the source
commit. Full results are recorded in `recipe-verification.json`. These test recipe consistency and safety,
not model behavior or GPU qualification. A source commit is made before publication;
final commit/push identifiers are given in the turn result to avoid self-reference.

Historical receipt status/visibility fields describe their dated transactions, not
current publication. The authoritative current publication receipt is `public-release.json`.
