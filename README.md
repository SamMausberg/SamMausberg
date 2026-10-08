# Sam Mausberg

I work on GPU inference, kernels and compilers in Vancouver. I built [FindTensor](https://findtensor.com), an experimental compiler and runtime, and previously researched GPU architecture with Tor Aamodt at UBC. I'm looking for a full-time engineering role.

[Website](https://sammausberg.com) · [Email](mailto:samuelmausberg@gmail.com) · [LinkedIn](https://www.linkedin.com/in/sam-mausberg/) · [ORCID](https://orcid.org/0009-0006-1091-8044)

## Selected work

- [CAIRN](https://github.com/SamMausberg/cairn) — experimental CPU/GPU language and compiler, with ownership checks and kernel validation.
- [The Work a Verifier Needs](https://github.com/SamMausberg/verified-progress) — SGLang inference optimizations and int8 output-head screening, measured on GH200.
- [B200 kernels](https://github.com/SamMausberg/sol-execbench-b200-kernels) — 2.94× average speedup on Hyena convolution/gating against the official SOL-ExecBench v1.1 scoring baseline.
- [Command A+ benchmarks](https://github.com/SamMausberg/capp-vllm-bench) — 25–82% higher aggregate decode throughput versus defaults on random-token workloads across two H100s.

## Upstream contributions

- **FlashInfer:** merged [CUDA-graph MoE padding fix](https://github.com/flashinfer-ai/flashinfer/pull/5451); [dispatch diagnostics and configuration API](https://github.com/flashinfer-ai/flashinfer/pull/4802) incorporated with attribution; [FP8 calibration bug](https://github.com/flashinfer-ai/flashinfer/pull/4984) reported and reproduced.
- **NVIDIA CCCL / CUB:** merged execution-environment support for [merge sort](https://github.com/NVIDIA/cccl/pull/11587), [merge](https://github.com/NVIDIA/cccl/pull/11589) and [batched memcpy](https://github.com/NVIDIA/cccl/pull/11590).
- **Accel-Sim:** merged [Ubuntu 24.04 / CUDA 13.1 container update](https://github.com/accel-sim/Dockerfile/pull/11).

<details>
<summary>More projects</summary>

- [KernelIndex](https://github.com/SamMausberg/KernelIndex) — GPU benchmark search with source provenance.
- [H100 serving estimator](https://github.com/SamMausberg/h100-serving-estimator) — GPU-time estimates from 91 runs, with held-out evaluation.
- [SmolLM2 CPU checks](https://github.com/SamMausberg/smollm2-cpu-conformance) and [tensor parallel reference](https://github.com/SamMausberg/tensor-parallel-reference) — numerical conformance and fault containment.
- **GPU MODE:** H100 [prefix sum](https://www.gpumode.com/leaderboard/541?tab=rankings), [histogram](https://www.gpumode.com/leaderboard/539?tab=rankings), [matrix multiplication](https://www.gpumode.com/leaderboard/540?tab=rankings) and [convolution](https://www.gpumode.com/leaderboard/537?tab=rankings); B200 [vector addition](https://www.gpumode.com/leaderboard/543?tab=rankings) and [grayscale conversion](https://www.gpumode.com/leaderboard/538?tab=rankings).

</details>

<details>
<summary>Research manuscripts and proofs</summary>

Independent preprints and manuscripts, with supporting code and selected Lean proofs.

- **Attention:** [exact attention I/O bounds](https://github.com/SamMausberg/exact-attention-io-lower-bound), [near-linear attention in 3D](https://github.com/SamMausberg/near-linear-attention-3d) and [reachable-state certificates](https://github.com/SamMausberg/attention-reachable-public-replay).
- **Learning:** [SQ learning and dimension complexity](https://github.com/SamMausberg/sq-dimension-research) and [bounded-time logistic SGD](https://github.com/SamMausberg/gaussian-sgd-ordinary).
- **Privacy:** [adaptive shuffled Gaussian accounting](https://github.com/SamMausberg/adaptive-shuffled-gaussian-accounting).
- **Physics:** [memory return](https://github.com/SamMausberg/returning-constructor), [mechanical mediation](https://github.com/SamMausberg/mechanical-mediation), [information tasks and Bell bounds](https://github.com/SamMausberg/information-tasks-bell-bounds) and [constructor entropy](https://github.com/SamMausberg/constructor-entropy).
- **Lean:** [Erdős problems](https://github.com/SamMausberg/lean-formalizations).

</details>

<details>
<summary>Other contributions and proposals</summary>

Open pull requests:

- [FlashInfer](https://github.com/flashinfer-ai/flashinfer/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg) and [CUB / Thrust](https://github.com/NVIDIA/cccl/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg).
- **SGLang:** [verification](https://github.com/sgl-project/sglang/pull/42209), [planning](https://github.com/sgl-project/sglang/pull/42195) and [serving fixes](https://github.com/sgl-project/sglang/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg).
- [GPU MODE QR benchmark checks](https://github.com/gpu-mode/reference-kernels/pull/170), [torchcomms extension packaging](https://github.com/meta-pytorch/torchcomms/pull/3688) and [Accel-Sim application compatibility](https://github.com/accel-sim/gpu-app-collection/pull/85).

Closed without merge: [Triton FP8 dot product](https://github.com/triton-lang/triton/pull/11386) and [GPGPU-Sim CUDA 13](https://github.com/accel-sim/gpgpu-sim_distribution/pull/134).

</details>
