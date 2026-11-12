# Optional GLP-39 runtime steering

**Default: OFF.** Stock DeepSeek-V4.1-Flash-1017 is usable without a vector. Packaging a direction file does not activate it and does not modify model weights.

## What it does

msuiche's GLP-39 is a **spec-v1** projective direction file for the `residual_stream_post_layer` hook. At selected layer boundaries, the engine folds the layer write into the four residual streams using a rounded multiply followed by four FP32 FMAs, rounds to BF16, and projects each stream independently:

```text
h <- h - alpha * dot(h, direction[layer]) * direction[layer]
```

The implementation preserves the reference's 320-thread × 16-column projection/reduction order. Decode, verification and prefill use the corresponding post-layer boundary. The file selects **zero-based layers 1 through 39 inclusive**, leaving layer 0 alone; the tested **alpha is 0.75**. This is GLP-39 only, not the different GLP-27/spec-v3 pre-Engram method.

## Enable / disable

The bundled-image supervisor has an explicit runtime flag on **every rank**:

```sh
# Default, including when the optional vector is in the image:
python3 /opt/recipe/entrypoint.py --rank RANK --fleet /etc/pico/fleet.conf --steering off
# Opt in:
python3 /opt/recipe/entrypoint.py --rank RANK --fleet /etc/pico/fleet.conf --steering glp39
```

Direct engine users instead set `WEIGHTLESS_STEER_PATH` before launch. The file supplies alpha and layers; `WEIGHTLESS_STEER_ALPHA=0.75` is the tested override. Leaving `WEIGHTLESS_STEER_PATH` **unset** disables the hook. Alpha zero preserves the unsteered path while still validating the file. The supervisor clears all steering variables in OFF mode, so an inherited environment cannot silently enable it.

Malformed metadata, unsupported hooks/specs or invalid directions must fail startup, never silently fall back. Do not synthesize a replacement vector or infer equivalence from the filename.

## Artifact and license

Author: **msuiche**. Public source: [GLP-39 model repository](https://huggingface.co/msuiche/DeepSeek-V4.1-Flash-1017-abliterated-cyber-GLP-39-L1-39-a0.75). Published filename:

`glp.deepseek-v41-flash-1017-GLP-39-L1-39-a0.75.gguf`

The tested full-file SHA256 is `9c66d47701e0ceb42c33906f2d3789c0f1f16b21e7d97185f20f7f3f09fbf5cf` (homeinfra `docs/operations/evidence/pico-glp-upstream-prepare-20261107/README.md`). Verify that exact digest before bundling as `bundle/vectors/glp39.gguf`. The publisher's public model-card metadata declares **MIT**; the base model is also MIT. The vector is optional and is **not downloaded or included in this Git repository**. Retain author/license notices when obtaining it; any hosting access terms must also be respected.

## Recorded validation, not fresh recipe validation

`docs/operations/evidence/pico-glp-upstream-prepare-20261107/README.md` records **0 reference-arithmetic differences** over 798,720 folded values and 156 dot rows. The current vision qualification at homeinfra `cf6e8b67c`, `docs/operations/evidence/pico-image-support-20261111/retrial-spark-only/REPORT.md`, records **9/9 OFF + 9/9 alpha-zero** bit-identical identity (including the 1M needle) and **88/88 image QA with steering OFF + 88/88 with GLP-39**. Native image support and steering are independent switches. The generic launcher enables vision by default while leaving steering OFF. Image-bearing histories are intentionally uncached; changing the steering configuration is not an image-prefix cache feature.

The distribution candidate uses the generic supervisor with steering OFF. It contains
the authentic optional vector but does not activate it. Production used a different
private launcher; its defaults must not be inferred from this recipe. The candidate
still needs its own GPU acceptance; see [build gaps](build.md#residual-gaps).
