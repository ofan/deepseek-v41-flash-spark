# Client-only HLE adapter

This wrapper adds HTTP generation to the existing DeepInfer HLE evaluator. It does
not launch an engine, invent questions or replace the existing LLM grading. It
never changes steering, clocks, routing or saved sessions. The recipe defaults to
GLP-39 ON at alpha 0.75, layers 1–39, with explicit `--steering off` opt-out; an HLE
steering-ON measurement still requires verification of the server's actual state.

**Current result: not run, zero scored HLE samples.** The pinned official dataset
is now staged and locally verified at 2,158 text-only questions. The run is stopped
by the production 32,768-token output cap, which is below the official 256K
recommendation and truncates about half of the diagnostic questions. See the
[dataset receipt and protocol caveat](benchmarks.md#standardized-quality-comparison--dataset-staged).
The implementation is offline-tested, not yet validated on scored HLE generations.

## Sources and installation

- Evaluator: [DeepInfer](https://github.com/deepseek-ai/DeepInfer), commit
  `774ce244b87cc0eb8d4b94ab9f5de2ab22049f01`, unchanged subset in
  [`vendor/hle-evaluator`](../vendor/hle-evaluator), Apache-2.0. File hashes are
  checked before use. No offline engine dependency is required.
- Dataset: [official cais/hle](https://huggingface.co/datasets/cais/hle), revision
  `5a81a4c7271a2a2a312b9a690f0c2fde837e4c29`, `test` split. Obtain authorization
  under its terms first. The script does not accept terms or redistribute data.
- [Official model-card reference](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/main/README.md):
  **44.0% HLE without tools, text-only**, not the 42.6% full-set score.

```sh
python3 -m venv work/hle-env
. work/hle-env/bin/activate
python3 -m pip install -r requirements-hle.txt
```

Keep datasets, gold answers, generated text and judge responses in a **private
directory outside this public checkout**. The CLI enforces that boundary and
creates state with restrictive permissions. Supply credentials through the named
environment variables using your own secret manager; do not put secrets in command
arguments, logs or committed files. This repository embeds no deployment endpoint.

## Stage the official dataset

Set `HLE_PRIVATE_DIR` to your private output directory and populate `HF_TOKEN`
transiently with your authorized read token. Then:

```sh
python3 -B scripts/hle-http.py stage --directory "$HLE_PRIVATE_DIR/data"
```

The script downloads the pinned parquet, preserves source order and the exact
question/answer strings, and filters images using the existing evaluator's
`_has_image` predicate. It writes `hle-text.jsonl` and `dataset-provenance.json`
with source, revision, actual counts and hashes. It does not use a mirror or make
up a replacement set. The documented 2,158 text questions must be verified from
the actual authorized download, not assumed. A failed download writes access
metadata but **cannot** produce a staged-data receipt or score.

## Freeze generation and judge settings before starting

Verify the server's exact checkpoint, engine, GLP settings, output cap and context.
Do not infer the server output cap from a client's requested `max_tokens` value.
The adapter defaults are one concurrent request, one sample per question,
temperature1, top-p1, thinking ON, effort100, output budget262144 and no tools.
The per-question seed is the source-order index, matching the offline one-sample
seed plan. HTTP uses the live frontend's message renderer, not the offline
checkpoint encoder; that distinction must be disclosed.

**Production caveat:** the currently inspected server uses its compiled
**32,768-token output cap**, while the official card recommends **at least256K**.
The adapter refuses a requested output budget above the verified cap. For an
unchanged-production run, explicitly set the output budget to32768 and record this
setting difference. A larger output cap requires separate serving authorization;
this script cannot change it. Do not call a shortened-budget measurement an exact
reproduction of the official settings.

Freeze the judge model and these existing scorer variables **before generation**:
`EVAL_JUDGE_BASE_URL`, `EVAL_JUDGE_API_KEY`, `EVAL_JUDGE_MODEL`. The scorer is
unmodified: its HLE prompt and parser, temperature1, top-p0.95 and max output65536
are retained. The official card does not identify its judge, so disclose the model
you use. No judge model is hard-coded or silently selected by this recipe.

## Read-only load observer

`--load-command` is mandatory. Supply your own **read-only** monitor executable
that prints exactly a JSON object with nonnegative integer `external_active`,
counting other active/admitted requests on the same engine. **Exclude this
adapter's own requests**, and include direct clients as well as any gateway
clients. Validate that accounting independently before a shared-production run.
The command is split as arguments, not executed by a shell. It must return within
10seconds. Do not place credentials in its argument string.

New samples wait while other work is active; the default wait budget is300seconds.
A monitor runs every5seconds. At least four external requests in three consecutive
samples stops this client's wave. Monitor failure stops closed. This is a
conservative load signal, **not a proof of fair scheduling**: if existing sessions
show starvation, interrupt the adapter immediately. It preserves completed samples
for resume and never resets server sessions.

## Run and resume

Set `HLE_BASE_URL` to your server's Chat Completions base URL (ending in `/v1`),
`HLE_MODEL` to its exact model ID, and `HLE_LOAD_MONITOR` to your validated observer.
Set `HLE_API_KEY` transiently if your endpoint needs authentication. Set
`HLE_SERVER_OUTPUT_CAP` from the live server and `HLE_OUTPUT_BUDGET` to the explicit
frozen budget at or below that cap.

```sh
python3 -B scripts/hle-http.py run \
  --base-url "$HLE_BASE_URL" --model "$HLE_MODEL" \
  --data-file "$HLE_PRIVATE_DIR/data/hle-text.jsonl" \
  --provenance "$HLE_PRIVATE_DIR/data/dataset-provenance.json" \
  --out-dir "$HLE_PRIVATE_DIR/run" \
  --server-max-tokens "$HLE_SERVER_OUTPUT_CAP" \
  --max-tokens "$HLE_OUTPUT_BUDGET" \
  --load-command "$HLE_LOAD_MONITOR"
```

There is no subset/limit option. Reuse the identical command and private output
directory to resume. Dataset hash, source revision, adapter hash, generation
settings and model ID are frozen in `meta.json`; mismatches stop resume. A completed
sample is fsynced to `raw_rank000.jsonl`. Torn, duplicate, unknown or mismatched
rows are errors, never silently discarded. No complete sample is regenerated on
resume. Output-budget truncations remain results, not retry opportunities.

At most one bounded wave is submitted. HTTP errors, incomplete streams, missing
usage and unexpected tool calls stop the wave; there is no blind retry loop.
Default per-request wall deadline is7200seconds, connect timeout10seconds and
stream-idle timeout30seconds. Slow requests that exceed these bounds stop and
checkpoint, rather than receiving a false score. No cost or completion-time
promise is made for the full HLE set.

## Score using the unchanged evaluator

Only after complete generation coverage:

```sh
python3 -B scripts/hle-http.py score \
  --out-dir "$HLE_PRIVATE_DIR/run" \
  --provenance "$HLE_PRIVATE_DIR/data/dataset-provenance.json"
```

This invokes unchanged `eval/score.py --judge llm`, with judge concurrency1 by
default. Its normalized exact-match helper is smoke-only, **never** the reported
HLE score. The frontend's final answer content is passed in full; separately
streamed reasoning is not graded, matching the scorer's thinking-section exclusion.
Unparsed judge responses, invalid outputs or incomplete coverage prevent a
publishable result. Truncated outputs are counted unchanged and must be reported.

Keep `raw_rank000.jsonl`, `scored.jsonl` and judge responses private. Publish only
sanitized per-sample IDs/hashes, verdicts, token usage/timings and aggregate
`summary.json` fields, with dataset/adapter/scorer hashes, coverage, finish reasons,
truncations, judge settings and all known differences from the official run. Do
not publish questions, reference answers, generated prose, endpoints or credentials.
The percentage-point delta is `measured HLE percent − 44.0` only after a complete
valid scored run. Zero samples is **not** a score of zero percent.
