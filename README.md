# Sam Mausberg

I work on GPU inference, kernels and compilers in Vancouver. I built [FindTensor](https://findtensor.com), an experimental LLM compiler and runtime, with Claude Code and Codex agents working to my design. I previously researched GPU architecture with Tor Aamodt at UBC. I'm looking for a full-time engineering role.

[Website](https://sammausberg.com) · [Email](mailto:samuelmausberg@gmail.com) · [LinkedIn](https://www.linkedin.com/in/sam-mausberg/) · [ORCID](https://orcid.org/0009-0006-1091-8044)

## Selected work

- [CAIRN](https://github.com/SamMausberg/cairn): experimental CPU/GPU language and compiler, with ownership checks and kernel validation. Claude Code agents wrote most of the code to my design. Its first GH200 run turned up an NVVM 7.0.1 loop-exit miscompile, reduced to 8 lines with a workaround in [#164](https://github.com/SamMausberg/cairn/pull/164).
- [The Work a Verifier Needs](https://github.com/SamMausberg/verified-progress): SGLang inference optimizations and int8 output-head screening, measured on GH200. In DFlash speculative decoding of Qwen3.5-4B, verifying draft blocks without per-position state snapshots, narrowing the verify tiles and enabling FlashAttention 4 raised per-request output 8.4–9.3% at 1–4 concurrent requests and throughput 12.4–13.7% at 8–32, over tuned stock SGLang. AI-assisted.
- [B200 kernels](https://github.com/SamMausberg/sol-execbench-b200-kernels): official NVIDIA SOL-ExecBench v1.1 evaluations, with geometric-mean speedups over NVIDIA's agent-optimized scoring baseline of [2.94×](https://research.nvidia.com/benchmarks/sol-execbench/submission/41305) on Hyena convolution/gating, [2.52×](https://research.nvidia.com/benchmarks/sol-execbench/submission/36921) on linear/GELU/GRN/linear, [1.52×](https://research.nvidia.com/benchmarks/sol-execbench/submission/42805) on QKV projection/GQA reshape and [1.27×](https://research.nvidia.com/benchmarks/sol-execbench/submission/36700) on FP8 gate/up projection.
- [Command A+ benchmarks](https://github.com/SamMausberg/capp-vllm-bench): on two H100s, giving the KV cache the memory vLLM left unused raised KV capacity 1.79× and end-to-end output throughput 4–34% at each context's largest batch (25–82% in steady-state decode), on random-token workloads.

## Upstream contributions

- **FlashInfer:** merged [CUDA-graph MoE padding fix](https://github.com/flashinfer-ai/flashinfer/pull/5451), shipped in v0.7.1 and extended by NVIDIA in [#5977](https://github.com/flashinfer-ai/flashinfer/pull/5977); [dispatch diagnostics and configuration API](https://github.com/flashinfer-ai/flashinfer/pull/4802) incorporated with co-author credit; [FP8 calibration bug](https://github.com/flashinfer-ai/flashinfer/pull/4984) reported and reproduced, credited in the fix.
- **NVIDIA CCCL / CUB:** merged execution-environment support for [merge sort](https://github.com/NVIDIA/cccl/pull/11587), [merge](https://github.com/NVIDIA/cccl/pull/11589) and [batched memcpy](https://github.com/NVIDIA/cccl/pull/11590).
- **Accel-Sim:** merged [Ubuntu 24.04 / CUDA 13.1 container update](https://github.com/accel-sim/Dockerfile/pull/11).

<details>
<summary>More projects</summary>

- [KernelIndex](https://github.com/SamMausberg/KernelIndex): GPU benchmark search with source provenance.
- [H100 serving estimator](https://github.com/SamMausberg/h100-serving-estimator): GPU-time estimates from 91 runs, with held-out evaluation.
- [SmolLM2 CPU checks](https://github.com/SamMausberg/smollm2-cpu-conformance) and [tensor parallel reference](https://github.com/SamMausberg/tensor-parallel-reference): numerical conformance and fault containment.
- **GPU MODE** PMPP practice boards, ranks as of Oct 16, 2026: H100 [prefix sum](https://www.gpumode.com/leaderboard/541?tab=rankings) 2nd of 27 (1st from Sep 2 to 30), [histogram](https://www.gpumode.com/leaderboard/539?tab=rankings) 3rd of 27, [matrix multiplication](https://www.gpumode.com/leaderboard/540?tab=rankings) 6th of 38 and [convolution](https://www.gpumode.com/leaderboard/537?tab=rankings) 6th of 31; B200 [vector addition](https://www.gpumode.com/leaderboard/543?tab=rankings) 4th of 63 and [grayscale conversion](https://www.gpumode.com/leaderboard/538?tab=rankings) 3rd of 43.

</details>

<details>
<summary>Research manuscripts and proofs</summary>

Independent preprints and manuscripts, with supporting code and selected Lean proofs.

- **Attention:** [exact attention I/O bounds](https://github.com/SamMausberg/exact-attention-io-lower-bound), [near-linear attention in 3D](https://github.com/SamMausberg/near-linear-attention-3d), [reachable-state certificates](https://github.com/SamMausberg/attention-reachable-public-replay) and [exact neural sampling](https://github.com/SamMausberg/exact-sampling-networks).
- **Learning:** [SQ learning and dimension complexity](https://github.com/SamMausberg/sq-dimension-research), [bounded-time logistic SGD](https://github.com/SamMausberg/gaussian-sgd-ordinary) and [low-logit-rank distributions](https://github.com/SamMausberg/low-logit-rank-distillation).
- **Inference:** [certified int8 output heads](https://github.com/SamMausberg/verified-progress).
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
