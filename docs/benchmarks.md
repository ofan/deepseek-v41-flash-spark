# Recorded benchmarks and evidence

These are **historical recorded results**, not measurements of this scaffold or a newly built GHCR image. Hardware target: four GB10 / DGX Spark-class machines, TP4. Rates are tokens per second. Cold prefill is actual prompt tokens divided by TTFT; concurrency decode is total completion tokens divided by full-wave wall time, not per-stream throughput. The acceptance method used thinking off, temperature 0, seed 42, a fixed saved corpus, 128-token needle cap and 256-token prose decode [B].

Evidence is in the homeinfra repository, branch `glp/pico-glp-steer-20261106`, snapshot `f2a0a4dbea07ac9bf94bb24d8605da8f43a9a099`. Paths below identify private provenance without copying request captures or infrastructure details.

## Sampler production image

Version `2026.11.08-sampler-open-unit-r1`, engine `d04020c`, stock 1017 + GLP-39 alpha 0.75, layers 1–39. Figures rounded for presentation; original precision is preserved in [A]. **Steering is ON in these measurements, although this public recipe defaults OFF.**

| Measurement | Reported rate | Evidence |
|---|---:|---|
| Prefill 32K | **8,999** | [A], `README.md`, Fresh qualification (8999.005) |
| Prefill 131K | **9,380** | [A], `README.md`, Fresh qualification (9380.171) |
| Decode, single stream | **88.6** | [A], `README.md`, Fresh qualification (88.636) |

## Historical r5 comparison baselines

These are the campaign's reused **r5-comparator baselines**, not fresh runs. Important provenance distinction: [B] prints these numbers in its **Prior Pico** column; the repaired r5 measurements in its **Fixed r5** column differ. Later steering windows reused the prior baseline under the production/r5 comparator label [C]. Do not silently attribute the comparison column to a new repaired-r5 measurement.

| Measurement | Reported baseline rate | Evidence |
|---|---:|---|
| Prefill 32K | **9,098.9** | [B], Standard acceptance, Prior Pico (9098.916); reused in [C] |
| Prefill 131K | **9,479.4** | [B], Standard acceptance, Prior Pico (9479.384); reused in [C] |
| Decode c1 | **82.2** | [B], Standard acceptance, Prior Pico (82.221); reused in [C] |
| Decode c4 | **155.0** | [B], Standard acceptance, Prior Pico (155.007) |
| Decode c16 | **259.5** | [B], Standard acceptance, Prior Pico (259.496); reused in [C] |

## Capacity and correctness

| Property / check | Recorded result | Evidence |
|---|---|---|
| Active slots | **16** | [B], Build/source/live end state; [A], Fresh qualification |
| Context per slot | **1,048,576 tokens** | [B], Build/source/live end state |
| Needle at approximately 500K | **Exact**, actual prompt 500,025 tokens | [C], Gate scoreboard; [D], Qualification |
| Needle at approximately 1M | **Exact**, actual prompt 1,048,025 tokens | [C], Gate scoreboard; [D], Qualification |
| Combined capability / needle points | **14/14** stock and **14/14** steered, **0-point loss** | [C], Gate scoreboard; reaffirmed 14/14 in [A] |
| Steering OFF / alpha-zero identity | **9/9 + 9/9**, bit-identical to recorded controls, including 1M needle | [A], Fresh qualification |
| Stability | **16/16** streams; **0** restarts, OOMs and failed measured requests | [A], Fresh qualification |
| Saved-session tier per rank | **3 GiB RAM + 160 GiB SSD** | [B], Root cause / Build/source/live end state; [D] |
| Free-space guard | **32 GiB** | [B], Root cause and fix |

The “14/14 capability battery” is a combined point total, not 14 independent capability prompts: adoption capability **6** + needles **2** + P5 capability **6** [C]. The frontend's **160M-token** retained-history LRU is distinct from **16** simultaneously active slots; it includes generated tokens, has a separate **256-session** cap and promises no cross-restart retention [B].

## Evidence directories

- **[A]** `docs/operations/evidence/pico-token-corruption-20261108/` — sampler production qualification, `README.md`; named raw speed receipt `speed-spots.json` (not copied into this package).
- **[B]** `docs/operations/evidence/pico-session-cache-fix-20261106/` — method, prior/fixed baseline table, cache/slot/context contract, `README.md`.
- **[C]** `docs/operations/evidence/pico-glp-r4-window-20261106/` — official-stock vs steered quality, exact needle lengths and comparator reuse, `README.md`.
- **[D]** `docs/operations/evidence/pico-glp-promotion-20261107/` — full-spill promotion qualification, `README.md`.

Only the reports were used to prepare this publication; no raw request, tokenizer, generated response or image-support artifact is included. Benchmark throughput is workload-specific and not a hardware guarantee.
