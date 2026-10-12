# ProtoMotions versus RSL-RL distillation verification

## Scope and conclusion

Source review of local ProtoMotions commit `7a8417a9f55b1586b0d6e8f46578c5bc9d7ce1f1` and RSL-RL tag `v5.5.1`, commit `857de6165c5fd479726ec8ac5c9303a497766f30`. Both checkouts were clean when inspected. This section establishes source behavior, not numerical equivalence or simulator training quality.

**They share the online teacher-labeling / supervised imitation principle. They are not identical complete training algorithms.** A deliberately configured, feedforward ProtoMotions student can implement the same action-MSE objective. ProtoMotions' MaskedMimic preset instead trains a privileged posterior plus a deployable prior and is not an RSL-RL distillation replica.

References below use `PM` for `external/ProtoMotions/protomotions` and `RSL` for `/home/android/workspace/github/mujocolab/rsl_rl/rsl_rl`.

## Behavior side by side

| Concern | ProtoMotions | RSL-RL 5.5.1 | Assessment |
|---|---|---|---|
| Labels | Calls external expert on the current observations before the environment step; prefers `mean_action`, falling back to `action`; saves `expert_actions`. | Calls teacher on current observations before the step with deterministic output; saves `privileged_actions`. | Same label timing and deterministic PPO-teacher target. PM fallback can be stochastic for other model contracts. |
| Teacher inputs | Explicit `expert_` observation keys mapped to the teacher's original keys. | Configured teacher observation group from the shared TensorDict. | Both allow privileged teacher observations; experiment must supply equivalent features. |
| Rollout actor | Configurable STUDENT or EXPERT; STUDENT selects `privileged_action` when present. | Always student; requests stochastic output, which samples only when a distribution is configured. | Same state distribution only for suitably configured plain students. Expert rollouts are a different option. |
| Teacher fixed | Expert in eval mode, parameters `requires_grad=False`, labeling under `no_grad`; optimizer contains student only. | Teacher in eval mode, labels collected under runner `inference_mode` and detached; optimizer contains student only. | Teacher is effectively fixed in both; RSL does not require setting every teacher parameter's `requires_grad=False`. |
| Core loss | Configurable MSE, discrete cross entropy, discrete/Gaussian KL; weighted loss and optional model/extra losses. | Mean action MSE or Huber; no return target. | MSE matches only with the correct prediction/target tensors, weight 1, and no extra losses. Huber is absent from PM's shared supervision options. |
| Rewards | Recorded by common agent; generic supervision does not use them as targets. | Recorded; `compute_returns` is a no-op. | Both perform supervised imitation, not PPO reward optimization, in this path. |
| Optimization | Flattens environment/time samples, shuffles minibatches, updates optimizer once per minibatch, repeats mini-epochs. | Replays chronological time slices across all environments; sums losses over `gradient_length` before each optimizer step. | Different batching, ordering, gradient scale, and optimizer-step counts. Same learning rate is not an equivalence setting. |
| Recurrent training | Generic supervised dataset is shuffled and flat; model-owned per-transition context can be replayed, but this is not RSL's sequence training loop. | Carries/reset/detaches RNN state, truncated backpropagation through time. | No generic recurrent equivalence claim. PM transformers with explicit history observations are not automatically RNN training. |
| Student normalization | Standard `NormObsBase` normalizes then updates moments on training forwards; repeated minibatch/epoch passes count again. Rollout is eval mode. | Explicit normalizer update once after optimization using the complete rollout. | Different statistics and timing, including changing normalization within PM optimization. |
| Episode state | Resets student model-owned rollout context on done; external expert initialized once. | Resets student and teacher on dones. | PM external stateful expert lifecycle needs attention; stateless teachers are unaffected. |
| Checkpoint | Saves student/model, supervised optimizer, common counters and evaluator state; external expert loaded again from configured checkpoint path. | Saves student, teacher, optimizer; runner adds iteration and metadata. | PM resume depends on external expert artifact availability/identity. Neither establishes exact arbitrary mid-rollout replay. |

Source anchors: PM `agents/supervised/agent.py:192` (optimizer), `:239` (expert labels), `:259` (rollout source), `:291` (applied action), `:344` (loss), `:389` (checkpoint); PM `agents/base_agent/agent.py:718` (rollout mode/label timing), `:939` (episode reset), `:1037` (optimization), `:1195` (dataset); PM `agents/utils/data.py:93` (flattening); PM `agents/common/common.py:134` (normalization); RSL `algorithms/distillation.py:116` (actions), `:123` (done handling), `:138` (returns), `:143` (update), `:205` (modes), `:216` (checkpoint); RSL `storage/rollout_storage.py:212` (time-ordered batches), `runners/on_policy_runner.py:66` and `:82` (modes/inference).

## MaskedMimic is a deliberate difference

MaskedMimic's `action` is the sparse-observation prior path. Its `privileged_action` is the privileged residual-posterior path. The generic agent's STUDENT rollout uses `privileged_action` when it exists, and the preset supervises that same output against the expert. The model adds KL regularization between posterior and prior, while inference uses the prior path. Thus the training policy is student-owned but privileged, rather than the deployable student used by plain RSL distillation.

Evidence: PM `agents/supervised/masked_mimic_model.py:121` (both paths), `:164` (inference), `:217` (KL contribution); `agents/supervised/masked_mimic_config.py:115` (preset); `agents/supervised/agent.py:291` (action selection). This is intended VAE behavior, not evidence of a bug.

## Configuration needed for the shared plain-distillation core

Use a plain feedforward student, a frozen external PPO teacher, `rollout_actor=STUDENT`, and `SupervisionLossConfig(loss_type=MSE, prediction_key="mean_action", target_key="expert_actions", weight=1.0)` when the student is a `PPOModel`. Disable additional model losses and match observation/action semantics. The generic default `prediction_key="privileged_action"` is intended for models producing that key and does not work unchanged with a plain PPO student.

Do **not** select PPOModel's `action` for differentiable MSE regression: `PPOActor.forward` uses `Normal.sample()`, while `mean_action` contains the differentiable mean (`PM agents/ppo/model.py:59`). A deterministic custom student's `action` can be differentiable, but that depends on its forward implementation.

For a numerical comparison, first turn normalization and stochastic/dropout effects off, use identical weights/input batches, and align loss reduction and optimizer steps. In RSL a `gradient_length=K` update sums K per-timestep mean losses instead of averaging them; setting `gradient_length=1` removes this particular scaling difference. PM shuffling must also be controlled. Agreement in this constrained test would verify the shared objective, not prove equal training trajectories under the default loops.

## Limitations and potential defects to track

1. **External stateful teacher reset:** PM initializes the expert's rollout context during creation but only resets `self.model` after episode completion. A custom external teacher requiring per-episode hidden/context reset can retain prior-episode state. A minimal runtime probe invoking the real `post_env_step_modifications()` with stateful student/expert stand-ins confirmed that a done row resets the student state but leaves expert state unchanged. This does not affect the usual stateless PPO teacher. No fix is included here. [Episode-reset hook](/home/android/workspace/protolab/external/ProtoMotions/protomotions/agents/base_agent/agent.py:924).
2. **RSL incomplete gradient window:** RSL explicitly warns that if `num_learning_epochs * num_steps_per_env` is not divisible by `gradient_length`, the remainder contributes to logged loss but is never backpropagated. With fewer total steps than `gradient_length`, no optimizer step occurs. This is documented current behavior, not a ProtoMotions discrepancy to copy.
3. **Configuration contracts:** Missing `privileged_action` with default loss, or non-differentiable sampled PPO `action` as prediction, are incorrect plain-student configurations rather than proof that the existing MaskedMimic training is broken.
4. **Artifact portability:** PM's external teacher is not embedded in the supervised checkpoint. Preserve and identify the exact expert artifact when resuming; changing that file changes the learning target.

## Executed CPU verification

**73 tests passed:** 5 new cross-library contract checks in [test_distillation_parity.py](/home/android/workspace/protolab/tests/test_distillation_parity.py), 56 existing ProtoMotions supervised/expert/MaskedMimic tests, and 12 RSL-RL 5.5.1 distillation tests.

The cross-library harness uses actual `SupervisedAgent` rollout, supervised-loss and optimizer-step methods, actual Lightning Fabric on CPU, and actual RSL-RL `Distillation`/storage. A thin TensorDict adapter gives both learners identically initialized RSL feed-forward networks so architecture differences cannot obscure algorithm differences. It bypasses ProtoMotions simulator/evaluator initialization; it is not an end-to-end training run.

Verified outcomes:

- Student rollout actions and pre-step deterministic teacher labels match with separate student/teacher observation inputs. ProtoMotions correctly prefers the expert's mean over a deliberately different sampled-action output.
- MSE losses and parameter gradients match on the same batch; neither teacher receives gradients.
- With normalization disabled, no auxiliary losses, matched temporal batches, Adam learning rate 0.001 and RSL `gradient_length=1`, student parameters match after each rollout update across 8 rollouts / 32 optimizer steps (`atol=1e-6`, `rtol=1e-5`). Imitation loss decreases and both teachers remain exactly unchanged.
- ProtoMotions' explicit EXPERT rollout mode executes teacher actions rather than student actions.
- Actual default-style ProtoMotions flat minibatching gives 4 optimizer steps for 4 timesteps x 4 environments with batch size 4, while RSL `gradient_length=2` gives 2 optimizer steps on that same rollout.
- A real ProtoMotions `PPOActor` produces a non-differentiable sampled `action` and a differentiable `mean_action`. The latter yields nonzero policy-network gradients through `SupervisedAgent.supervised_step()`.

Reproduce the new tests with:

```bash
MPLCONFIGDIR=/tmp/protolab-mpl OMP_NUM_THREADS=1 .venv/bin/python -m unittest tests.test_distillation_parity -v
```

Existing suites run: ProtoMotions `test_supervised_agent_flow.py`, `test_common_supervision.py`, `test_supervised_expert_utils.py`, `test_masked_mimic_supervised_loss.py`, `test_masked_mimic_model.py`; RSL-RL `tests/algorithms/test_distillation.py` at v5.5.1. The latter's tests were copied to temporary storage to avoid writes in the source checkout. Pytest and its dependencies were supplied from temporary storage, with plugin autoload disabled; they were not added to project dependencies.

No upstream implementation was changed by this review. Simulator-level policy quality, multi-GPU training and long-horizon recurrent correctness require separate experiments.
