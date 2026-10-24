# From LLM output to CBF constraints

This document answers reviewer comment 4 about how intents are mapped to CBF
constraints and which LLM is involved.

## 1. Intent format

An intent is a JSON object produced by the intent generator. For radio intents the
parameters that reach the filter are:

- `tx_power_dbm`: validated against the range 5.0 to 46.0 dBm, step 1.0
  (`llm-agent/intent/config_generator.py`, range table).
- `ho_hysteresis_db`: validated against the range 0.0 to 10.0 dB, step 0.5.

The CUE schema validator (`safety-filter/validators/cue_schema_validator.py`) is
Gate 1. It checks the structure and the allowed range of each field before any numeric
check is applied.

## 2. Which LLM

- **Production path, as coded:** the generator calls an OpenAI-compatible endpoint. The
  model name is read from `OPENAI_MODEL` (default `gpt-4`). A local backend reads
  `LOCAL_LLM_MODEL` (default `meta-llama/Llama-2-7b-chat-hf`).
- **Demo path:** `g4f` with `G4F_MODEL` (default `gpt-4`). This path is unofficial.
- **Generator used for the 50,000-intent campaign:** no language model. The campaign
  in `evaluation/statistical_analysis.py` (`generate_intent`) draws the current and
  requested state from uniform distributions, with 30 percent adversarial intents and
  8 percent malformed intents. Results obtained with it describe the filter on synthetic intents.
  Any claim about LLM behaviour must come from a separate experiment, which is not in
  this repository.

## 3. Mapping to barriers

1. Gate 1 (CUE schema) rejects malformed intents and out-of-range fields.
2. Gate 2 (CBF and Lyapunov), as implemented in the campaign (`gate2_cbf`):
   - Four linear barriers: h1 = 43 - P_tx, h2 = P_tx - 0, h3 = 100 - PRB, h4 = H_HO - 0.
   - If all barriers hold, the intent is accepted when V = ||x - x_ref||^2 < 5000 with
     x_ref = (30, 3, 50), and denied otherwise.
   - If a barrier is violated, the intent is amended by clamping the violating parameter:
     P_tx to 42 dBm (above the ceiling) or 1 dBm (below the floor), PRB to 95 percent,
     H_HO to 0.5 dB. The amended intent is accepted if all barriers then hold.
3. Gate 3 (Zeno guard) denies an intent that arrives less than tau_min = 200 ms after the
   previous actuation.

The stored acceptance rate (72.51 percent after the fix in `ERRATUM.md`) counts accepted
intents only. Accepted and amended together are 92.02 percent. The full breakdown,
including the cause of every denial, is in `evaluation/results/campaign_breakdown.md` and
per run in `evaluation/results/per_run.csv`.

## 4. Verified numbers of the campaign (v1.2)

Re-running `evaluation/statistical_analysis.py` (seeds run_id * 1000 + 42, 50 runs,
1000 intents each) gives:

- Accepted without amendment: 72.51 percent (mean 0.725100), 95 percent CI [0.721, 0.729].
- The reported "DSF latency" (about 1.58 ms) is not a measurement; see `LIMITATIONS.md`.
- Baseline violations: 212.1 per run; DSF violations: 0.0 per run.
