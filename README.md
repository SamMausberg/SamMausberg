# Sam Mausberg

GPU systems engineer focused on LLM inference, CUDA kernels and compilers. Based in Vancouver.

[Email](mailto:samuelmausberg@gmail.com) · [LinkedIn](https://www.linkedin.com/in/sam-mausberg/)

I'm building [FindTensor](https://findtensor.com), an experimental compiler and runtime for LLM inference in Rust, C++ and Python. Previously, I worked with Tor Aamodt at UBC on GPU architecture simulation.

## GPU systems and tools

- **[SOL-ExecBench B200 kernels](https://github.com/SamMausberg/sol-execbench-b200-kernels)**: CUDA C++, CuTe DSL and Triton kernels, with source packages and local B200 validation reports. Local scores are estimates, not confirmed leaderboard results.
- **[KernelIndex](https://github.com/SamMausberg/KernelIndex)**: A GPU performance index that compares matching workloads and links results to their source, environment and benchmark protocol. Imported results are labeled reported until independently reproduced by the index.
- **[Command A+ vLLM benchmarks](https://github.com/SamMausberg/capp-vllm-bench)**: A serving study on two H100s, covering prefill, decode, KV-cache capacity, CUDA graphs and tuning, with raw logs and a report.
- **[H100 serving estimator](https://github.com/SamMausberg/h100-serving-estimator)**: Estimates GPU-seconds per request from 91 published Command A+ runs, with held-out evaluation. Its accuracy and interval coverage depend on the workload; a simpler baseline wins on the unseen serving configuration.
- **[SmolLM2 CPU conformance](https://github.com/SamMausberg/smollm2-cpu-conformance)**: Separate full-sequence and incremental KV-cache implementations checked against Transformers across 48 numerical cases. A correctness study for one model revision on CPU.
- **[Tensor parallel reference](https://github.com/SamMausberg/tensor-parallel-reference)**: A CPU decoder block across 1, 2 and 4 worker processes, with numerical checks, exact wire accounting and 96 fault-injection cases.

## Language work

**[CAIRN](https://github.com/SamMausberg/cairn)** is an experimental systems language for CPU and NVIDIA GPU programs, designed to be written by AI agents. It compiles to C++20 and CUDA. The checker tracks ownership, task leases, effects and permitted parallel access patterns, with diagnostics that identify conflicts and suggest repairs. The repository includes the compiler, runtime, agent tools and benchmarks. Its Lean models cover specific rules; the compiler itself is not formally verified.

## Research

- **[The Work a Verifier Needs](https://github.com/SamMausberg/verified-progress)**: Certified output-head decisions and speculative-verification experiments on Qwen3.5-4B in SGLang on GH200. Includes a low-precision head with selective re-scoring and fallback to the stock kernel, Lean proofs for decision logic, and serving measurements across concurrency levels.
- **[StateCut](https://github.com/SamMausberg/statecut)**: Exact-reference attention certificates and persistent decoder-state writes, with scoped Lean proofs and GH200 experiments. Pretrained attention acceleration and equivalence to a deployed backend remain open.
- **[Contracted moment kernels](https://github.com/SamMausberg/contracted-moment-kernels)**: Moment summaries for certifying attention outputs, combining real-arithmetic proofs, exact-rational checks and CUDA experiments. The measured full pipeline remains slower than fused dense attention.
- **[Witness-CL](https://github.com/SamMausberg/witness-cl)**: Online executable memory for SQL agents, using delayed corroboration and replayable memory transitions. The implementation and development studies are public; the intended confirmatory efficacy claim is not established.
- **[SQ learning and dimension complexity](https://github.com/SamMausberg/sq-dimension-research)**: A manuscript on the separation between distribution-independent statistical-query learning and dimension complexity, with reproducible experiments and supporting Lean lemmas. The complete paper is not formalized.
- **[Memory return in quantum machines](https://github.com/SamMausberg/returning-constructor)**: A manuscript on repeated quantum transformations and memory reuse, with written proofs, exact finite checks, certified figure data and a partial Lean formalization. It has not yet been peer reviewed.
- **[Lean formalizations](https://github.com/SamMausberg/lean-formalizations)**: Formal models and proof development for Erdős problems in Lean 4 and mathlib. The workspace includes unfinished conjecture statements.

I use AI tools in research and implementation. The research repositories document that assistance and distinguish written proofs, compiled Lean results and empirical checks.

## Upstream contributions

- **FlashInfer**: My SM120 dispatch diagnostics and configuration API were [incorporated upstream](https://github.com/flashinfer-ai/flashinfer/pull/4802). My [fix for unrouted expert IDs in SM12x fused MoE](https://github.com/flashinfer-ai/flashinfer/pull/5451) was merged. I also reported and reproduced an [FP8 KV calibration bug](https://github.com/flashinfer-ai/flashinfer/pull/4984) that was fixed upstream. Further attention, GEMM, sampling and MoE work is in [open PRs](https://github.com/flashinfer-ai/flashinfer/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg).
- **NVIDIA CCCL / CUB**: Merged execution-environment support for [DeviceMergeSort](https://github.com/NVIDIA/cccl/pull/11587), [DeviceMerge](https://github.com/NVIDIA/cccl/pull/11589) and [DeviceMemcpy](https://github.com/NVIDIA/cccl/pull/11590). Further CUB and Thrust changes are [under review](https://github.com/NVIDIA/cccl/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg).
- **SGLang**: Open PRs for [snapshot-free GDN verification](https://github.com/sgl-project/sglang/pull/42209), [speculative planning from host-known lengths](https://github.com/sgl-project/sglang/pull/42195) and other [serving fixes](https://github.com/sgl-project/sglang/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg).
- **GPU MODE and torchcomms**: Open PRs for [QR benchmark input and stream checks](https://github.com/gpu-mode/reference-kernels/pull/170) and [building and shipping the uniflow Python extension](https://github.com/meta-pytorch/torchcomms/pull/3688).
- **Triton**: A [proposed SM120 FP8 dot rewrite using block-scaled MMA](https://github.com/triton-lang/triton/pull/11386), closed without merge.
- **Accel-Sim**: A merged [Ubuntu 24.04 / CUDA 13.1 container update](https://github.com/accel-sim/Dockerfile/pull/11), an open [GPU application compatibility PR](https://github.com/accel-sim/gpu-app-collection/pull/85), and a [GPGPU-Sim CUDA 13 proposal](https://github.com/accel-sim/gpgpu-sim_distribution/pull/134) closed without merge.
