# Production benchmarks and measurement receipts

Fresh decode results and retained acceptance results are separated below. Neither qualifies a new recipe build. Hardware: four GB10 / DGX Spark, TP4; stock DeepSeek-V4.1-Flash-1017, engine **b7c3eb5**, the **qualified private predecessor**. Source revisions and the historical production digest are in `sources.lock.json`.
These rates do not qualify the sanitized distribution candidate; its GPU serving qualification is pending. Steering was GLP-39 alpha0.75, layers1–39, except labeled OFF/alpha-zero arms. The recipe default remains OFF.


## Fresh decode battery (2026-11-13)

**Benchmarks measured with every GPU capped at 2,200 MHz (graphics clock).**

Read-only requests against the live production vision image `2026.11.08-native-vision-trial-r1`,
engine **b7c3eb5**, stock 1017 + GLP-39 alpha0.75, layers1–39, TP4,16 slots,1M context.
Every GPU has an **active configured 2,200 MHz graphics-clock cap**. Post-run samples
were 2,184–2,190 MHz; the numeric power limit is unavailable (`N/A`). This is a clock
cap, not a claimed wattage setting. No serving setting was changed.

| Streams | Prose decode tok/s | Code decode tok/s | Prose end-to-end tok/s | Code end-to-end tok/s |
|---:|---:|---:|---:|---:|
| 1 | 72.297 | 73.187 | 68.530 | 69.160 |
| 4 | 107.232 | 161.501 | 105.263 | 156.611 |
| 8 | 156.079 | 261.548 | 58.594 | 259.196 |
| 16 | 236.405 | 320.541 | 234.320 | 252.712 |

**58/58 requests succeeded**, each 256 output tokens, total14,848; zero request
errors and no observed container restarts/OOM. One bounded wave per cell, with
2seconds between waves, not a sustained-load or statistically repeated benchmark.
The server was shared production, not a reserved otherwise-idle test ring.

### Method and reproducibility

- Used the existing `bench.py` built-in **prose** and **code** prompts verbatim,
  filtered by their original dictionary keys; no authored/generated eval prompts.
  Each wave repeats that arm's prompt across its streams. It is **not a distinct-user
  prompt mix**, and cached/repeated input can affect first-token timings.
- Reused `multistream.http_streams` and `multistream.report`. Requests go directly
  to the rank0 frontend, streaming, temperature0, thinking disabled, max_tokens256,
 60-second HTTP timeout; stop on the first failing configuration.
- **Decode aggregate** = sum of `(completion_tokens - 1)` divided by
  `(latest completion time - earliest first-output-token time)` across the wave.
  At c1 this is per-stream decode; c4/c8/c16 are aggregate ring throughput.
- **End-to-end aggregate** = sum of completion tokens divided by
  `(latest completion time - earliest submission time)`. This includes first-token
  delay. It is distinct from decode throughput and from prefill throughput.
- The eight-stream prose wave had **21.882–23.619 seconds TTFT**; code at16 had
  **3.478–4.446 seconds TTFT**. The receipt does not attribute these delays. Decode
  throughput alone hides them. No latency or capacity guarantee follows from this run.
- Historical c1/c4/c16 rates below use different prompt mixtures/denominators;
  do **not** report the new prose/code numbers as a percentage regression against them.

Reproduce on your own idle/authorized server (no endpoint is embedded):

```sh
python3 scripts/benchmark-decode.py --url http://127.0.0.1:8888/v1 \
  --max-tokens 256 --timeout 60 --out decode.json
```

The wrapper imports this repository's included benchmark implementation. Measurement
receipts contain **timings, token counts, prompt/tool hashes and configuration only**,
not request text, generated text, endpoints or deployment identifiers:

- [Every configuration and request timing](benchmarks/2026-11-13-decode.json).
- [All four live GPU caps and restart/OOM counters](benchmarks/2026-11-13-gpu-cap.json).
- Vendored `bench.py` matches the measurement tool hash exactly. `multistream.py`
  differs only in a disclosed generic default data path; the source manifest records
  both hashes. Prompt hashes match the included built-ins. This documents the
  actual measured original tool rather than pretending the sanitized file was run.


## Retained accepted-production rates (2026-11-11)

| Measurement | tok/s (rounded) | Evidence |
|---|---:|---|
| Text prefill 32K | **8,951** | [V], Prefill baselines and gates (8951.37260359027) |
| Text prefill 131K | **9,259** | [V], same table (9259.254439942204) |
| Text prefill 500K | **9,076** | [V], same table (9076.005975294524) |
| Text prefill 1M | **8,598** | [V], same table (8598.31519705911) |
| Text decode single stream | **88.772** | [V], Remaining frozen gates (88.77236151328667) |
| Text decode c4, aggregate | **151.552** | [V], additional unchanged-suite observation |
| Text decode c16, aggregate | **269.804** | [V], additional unchanged-suite observation |

Prefill = server-counted prompt tokens / client time-to-first-token, with a one-token completion, unchanged adoption generator/calibration/suffix. Long targets were 500,025 / 1,048,025 text tokens; candidate actual prompt counts were 499,972 / 1,047,987. These are near-500K/1M measurements, **not exact maximum-context throughput**. Decode concurrency rate is aggregate completion tokens / full-wave wall time, not per-user rate. Workload-specific; no hardware guarantee.

## Accepted production correctness and capacity

| Check | Result | Evidence |
|---|---|---|
| Text identity, steering OFF | **9/9 bit-identical**, including 1M needle | [V], Remaining frozen gates |
| Text identity, alpha-zero | **9/9 bit-identical** | [V], same |
| Fixed image QA OFF | **88/88** correct | [V], six fixed cases, streaming/nonstreaming, repeated c1/c16 |
| Fixed image QA GLP-39 | **88/88** correct | [V], same matrix |
| Protocol | **12 rounds, zero leaks/errors** | [V], Remaining frozen gates |
| Stability | **16/16 streams, zero errors/restarts/OOM** | [V], Remaining frozen gates / final fleet |
| Text capability | **6/6** | [V], additional observations |
| Long needles | **2/2 exact**, established 500,025 / 1,048,025 targets | [V], additional observations; [Q], exact lengths |
| Active slots / context | **16 / 1,048,576** | [V], Candidate, packaging and settings |
| Saved-session RAM / SSD per rank | **3 GiB / 160 GiB**, **32 GiB** disk guard | [V], standing settings; [C], storage contract |

These counts do not claim 88 distinct image fixtures or 14 new capability cases. The fixed set has six known-answer images; 88 is the request/repeat/concurrency matrix size per steering arm. The current report records 6/6 capability plus 2/2 needles, not a newly rerun 14-point suite.

## Standardized quality comparison — not run

The comparison selected for this recipe is **HLE without tools, text-only subset**,
with GLP-39 **ON at alpha 0.75, layers 1–39**. DeepSeek's published reference is
**44.0%**. No steering comparison is planned; the local acceptance check below
remains a separate serving check.

| Benchmark | DeepSeek official | Recipe with GLP-39 ON | Recipe minus official |
|---|---:|---|---|
| HLE without tools, text-only | **44.0%** | **Not measured** | N/A |

**Run status: not run; samples 0; raw result absent; recipe score and delta null.**
No partial subset, exact-match smoke score, or local serving score is substituted
for an HLE result.

### Official published scores

[Official DeepSeek-V4.1-Flash-1017 model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/main/README.md),
retrieved **2026-11-14T16:09:57.174817+00:00**, HTTP **200**,
SHA-256 **`b72b796e4f4c739eca5d0ad360a7679b39118ca7eb64891f7151a527b292c42a`**. The scores below are copied from the
`DS-V4.1-Flash-1017` column, not another model's column:

| Benchmark | Official score (%) |
|---|---:|
| HLE w/o tools | 42.6 full; **44.0 text-only** |
| Terminal-Bench 4.0 | 42.3 |
| DeepSWE v1.1 | 77.0 |
| ProgramBench | 29.1 |
| NL2Repo-Bench | 68.2 |
| Automation-Bench v1.0.6 | 60.5 |
| Agents’ Last Exam | 35.4 |
| Apex Bench v1.1 | 72.1 |
| Chartography (w/tools) | 83.0 |
| BabyVision (w/tools) | 92.5 |
| ZeroBench-main (w/tools) | 51.0 |

For HLE, the daggered **44.0** is the **text-only subset**; **42.6** is the full
without-tools score. The text-only score is the intended reference, not 42.6.
The card lists temperature **1.0**, top-p **1.0**, **1M** context and at least
**256K** maximum output tokens. It does not state the evaluated sample count for
this row. There is no recipe run yet, so no actual run-setting comparison or
percentage-point delta is available.

### Exact tooling blocker

An existing HLE implementation was found in **DeepInfer**, source revision
**`774ce244b87cc0eb8d4b94ab9f5de2ab22049f01`**:

- `eval/hle/bench.py` constructs the existing HLE answer-format prompt and records.
- `eval/run_eval.py` is an **offline batch** generator. It imports `create_llm`,
  creates its own DeepInfer model and calls `llm.generate`. Its argument parser
  has **no HTTP endpoint / base-URL option**. Defaults include expert parallelism
  **8** and maximum **384 sequences**, not a bounded client against Pico's 16 slots.
- Its default HLE dataset, `eval/data/hle_test.jsonl`, is **not staged**.
  The tool documentation requires obtaining the official `cais/hle` dataset
  under its access terms. No questions were synthesized or substituted.
- `eval/score.py` requires an **LLM judge** for HLE. The included normalized-string
  equality function is explicitly smoke-only, not a comparable HLE evaluator.

The default Python environments on the build host and four GPU hosts, and the
serving container, did not have Inspect/Inspect Evals, lm-eval, LightEval or
Simple Evals available as an alternative HTTP-capable harness. This records the
inspected environments, not a claim that HLE is impossible or unavailable anywhere.

Running the offline launcher unchanged would not benchmark the production Pico
engine. Changing it into a client is outside the **unchanged existing tooling**
constraint. No offline model launch, serving change, engine restart or clock
change was made. No standardized benchmark requests were submitted.

### What is needed to obtain the score

Use an approved HTTP-capable HLE runner, or approve a client-only transport adapter
around the existing prompt builder and LLM scorer; preserve the standard questions
and scoring rather than authoring new prompts. Stage the official dataset under
its access terms and verify complete text-only coverage. Freeze the generation
budget, sampling settings, judge and bounded concurrency before starting; disclose
any differences from the official run. Keep GLP-39 ON, the graphics-clock caps at
2,200 MHz, and production otherwise unchanged. Only after complete scored coverage
can a recipe score and `recipe − 44.0` percentage-point delta be published.

[Machine-readable readiness and official-source record](benchmarks/2026-11-14-standardized-quality.json)
contains the explicit not-run status, null result/delta, evaluator source hashes
and remaining steps. It contains no dataset questions or generated answers.

## Local serving acceptance (2026-11-14)

This is the **completed small serving acceptance check**, not a standardized
model-quality benchmark. The fresh GLP-39 run scored **14/14 (100%)**:

| Component | GLP-39 ON, alpha 0.75 |
|---|---:|
| Adoption capability | **6/6** |
| Fixed long-context needles | **2/2** |
| P5 capability | **6/6** |
| **Combined serving acceptance** | **14/14** |

The checks are the existing serving-gate quality subset from [Q]. No new prompts
were authored. Default sequential concurrency **1**, stock 1017, engine **b7c3eb5**,
GLP-39 **alpha 0.75, layers 1–39**, 16 slots and 1,048,576-token context:

- Adoption capability and fixed needles: streaming, temperature **0**, seed **42**,
  thinking disabled, maximum **128 output tokens**. Unchanged retrieval inputs
  target **500,025** and **1,048,025** tokens; exact parsed JSON equality determines
  the needle verdict.
- P5 capability only: non-streaming, temperature **0.0**, reasoning effort **high**,
  maximum **8,192 tokens**, no seed set by the suite. Original per-case checks were
  unchanged; these include string checks, not comprehensive code execution.
- Client timeout **300 seconds per request**. The runner paused before submitting
  another check while other requests were admitted or in flight, with a
  **180-second** wait limit. It monitored load every **5 seconds**, stopping if
  at least **4** other requests persisted for **3 consecutive** observations.

The run completed **2026-11-14 15:41:13–15:45:33 UTC**, with **72** load observations
and at most **1** other admitted/in-flight request. It paused for other traffic;
there was no request error or sustained-contention abort. Sampled counters do not
exclude every user's latency impact. Production steering, routing and 2,200 MHz
caps were unchanged; container PIDs/start times and session-file identities/sizes
were preserved, with zero restarts or OOM kills. A real post-run completion returned
HTTP **200** from the expected serving backend.

[Original sanitized serving-check receipt](benchmarks/2026-11-14-quality.json)
retains all 14 verdicts, token usage, durations, prompt/answer hashes and source-tool
hashes. Its original comparison-planning metadata is historical, not the current
benchmark plan. The measured 14-check result is unchanged. It is not an HLE score,
and no numeric comparison between 14/14 and 44.0% is valid. This check does not
qualify the sanitized public runtime for four-rank GPU serving.

## Historical comparisons — not current production

| Historical version / measurement | tok/s | Evidence |
|---|---:|---|
| Sampler r1 text prefill 32K / 131K | 8,999 / 9,380 | [S]; standing baselines reused in [V] |
| Sampler r1 decode c1 | 88.6 | [S]; standing baseline reused in [V] |
| Prior Pico/r5-comparator prefill 32K / 131K | 9,098.9 / 9,479.4 | [C], **Prior Pico** column; reused by [Q] |
| Prior Pico/r5-comparator decode c1 / c4 / c16 | 82.2 / 155.0 / 259.5 | [C], **Prior Pico** column |
| Official-stock vs steered combined capability/needle points | 14/14 vs 14/14, delta0 | [Q], historical r4 gate |

The 14 points are adoption capability6 + needles2 + P5 capability6 [Q], not 14 independent current-vision prompts. [C]'s Fixed r5 column differs from its Prior Pico column; do not conflate them. Current prefill deltas against the sampler comparison are -0.5293%, -1.2873%, +0.0857%, -0.0119% at the four contexts, and decode +0.1945% [V].

## Evidence references

Homeinfra branch `glp/pico-glp-steer-20261106`. Current [V] is pinned at **cf6e8b67c8cb4c7a07dc52aaccf16f09fb39e774**; the other directories are retained historical evidence in that lineage.

- **[V]** `docs/operations/evidence/pico-image-support-20261111/retrial-spark-only/REPORT.md`: accepted current vision rates, QA, identity, protocol and stability.
- **[H]** `docs/operations/evidence/pico-image-support-20261108/window-r2/HOST-QUALIFICATION.md`: 266 tensors; 970,536,960 payload bytes; CPU reference6/6 and zero differing span elements. Host proof, not CUDA/CPU bitwise proof.
- **[S]** `docs/operations/evidence/pico-token-corruption-20261108/README.md`: historical sampler rates and combined14/14.
- **[C]** `docs/operations/evidence/pico-session-cache-fix-20261106/README.md`: method, prior/fixed comparison and session/spill contract.
- **[Q]** `docs/operations/evidence/pico-glp-r4-window-20261106/README.md`: historical14/14 quality and exact needle targets.

Only sanitized documentation/provenance is included here; no raw request, tokenizer, generated-response capture or test image payload is copied into the recipe.
