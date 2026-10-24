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
  8 percent malformed intents. The paper must describe this as a synthetic generator.
  Any claim about LLM behaviour must come from a separate experiment, which is not in
  this folder.

## 3. Mapping to barriers

1. Gate 1 (CUE schema) rejects malformed intents and out-of-range fields.
2. Gate 2 (CBF) takes each accepted field as a component of the state vector and checks
   the barrier constraint for the box barrier of that field. The filter returns one of
   three verdicts: accept, amend or deny. The author must confirm the amendment rule
   used by the conference code, because it is not written out in this folder.
3. Gate 3 (ZenoGuard) enforces the minimum inter-actuation interval tau_min before the
   verdict is applied.

The 49.4 percent acceptance figure counts "accepted" and "amended" together. The split
between accepted and amended, and the cause of each rejection, must be reported in the
paper from the raw results. They are not in this folder yet.

## 4. Verified numbers of the campaign

Re-running `evaluation/statistical_analysis.py` in this folder (seeds run_id * 1000 + 42,
N = 50 runs, 1000 intents each) reproduces:

- Acceptance rate: 49.36 percent (mean 0.493640), 95 percent CI [0.489, 0.498].
- Average DSF latency: 1.57 ms (the report stored in the repository gives 1.56 ms;
  this difference comes from the timing noise in the Python run).
- Baseline violations: 212.1 per run; DSF violations: 0.0 per run.
