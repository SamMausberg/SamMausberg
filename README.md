# Sam Mausberg

I work on GPU systems and compilers for LLM inference in Vancouver. I'm building [FindTensor](https://findtensor.com), an experimental inference compiler and runtime.

[Email](mailto:samuelmausberg@gmail.com) · [LinkedIn](https://www.linkedin.com/in/sam-mausberg/)

Previously, I worked with Tor Aamodt at UBC on GPU architecture simulation.

## Research

- [**The Work a Verifier Needs**](https://github.com/SamMausberg/verified-progress): Preprint on certified output-head decisions and speculative verification, studied on Qwen3.5-4B in SGLang on one GH200. Serving measurements and Lean proofs under stated rounding-error assumptions.
- [**A reachable-state separation between attention compression and its certificates**](https://github.com/SamMausberg/attention-reachable-public-replay): Manuscript with exact witnesses and SmolLM2-135M replay data, scoped to a specified certificate class. The dense control is faster.
- [**SQ learning and dimension complexity**](https://github.com/SamMausberg/sq-dimension-research): Manuscript on the separation between distribution-independent SQ learning and dimension complexity, with experiments and supporting Lean lemmas.
- [**Memory return in quantum machines**](https://github.com/SamMausberg/returning-constructor): Manuscript on repeated quantum transformations and memory reuse, with written proofs, exact finite checks and partial Lean formalization. Not yet peer reviewed.
- [**Lean formalizations**](https://github.com/SamMausberg/lean-formalizations): Erdős problems in Lean 4 and mathlib, including unfinished conjecture statements.

## Language design

[**CAIRN**](https://github.com/SamMausberg/cairn) is an experimental CPU/GPU systems language for AI agents, compiling to C++20 and CUDA. Its checker tracks ownership, leases, effects and parallel access. Lean proofs cover selected models; the compiler is not formally verified.

## Upstream contributions

- **FlashInfer**: Merged [SM12x MoE fix](https://github.com/flashinfer-ai/flashinfer/pull/5451); [SM120 diagnostics and configuration API](https://github.com/flashinfer-ai/flashinfer/pull/4802) incorporated upstream. Reported and reproduced an [FP8 KV calibration bug](https://github.com/flashinfer-ai/flashinfer/pull/4984), since fixed. Further [attention, GEMM, sampling and MoE PRs](https://github.com/flashinfer-ai/flashinfer/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg) remain open.
- **NVIDIA CCCL / CUB**: Merged environment support for [DeviceMergeSort](https://github.com/NVIDIA/cccl/pull/11587), [DeviceMerge](https://github.com/NVIDIA/cccl/pull/11589) and [DeviceMemcpy](https://github.com/NVIDIA/cccl/pull/11590). Further [CUB and Thrust changes](https://github.com/NVIDIA/cccl/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg) are under review.
- **SGLang**: Open PRs for [snapshot-free GDN verification](https://github.com/sgl-project/sglang/pull/42209), [host-based speculative planning](https://github.com/sgl-project/sglang/pull/42195) and [serving fixes](https://github.com/sgl-project/sglang/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg).
- **GPU MODE and torchcomms**: Open PRs for [QR benchmark input and stream checks](https://github.com/gpu-mode/reference-kernels/pull/170) and [building and shipping the uniflow Python extension](https://github.com/meta-pytorch/torchcomms/pull/3688).
- **Triton**: [SM120 FP8 dot proposal using block-scaled MMA](https://github.com/triton-lang/triton/pull/11386), closed without merge.
- **Accel-Sim**: Merged [Ubuntu 24.04 / CUDA 13.1 container update](https://github.com/accel-sim/Dockerfile/pull/11); [GPU application compatibility](https://github.com/accel-sim/gpu-app-collection/pull/85) under review; [GPGPU-Sim CUDA 13 proposal](https://github.com/accel-sim/gpgpu-sim_distribution/pull/134) closed without merge.

## GPU systems and tools

- [**SOL-ExecBench B200 kernels**](https://github.com/SamMausberg/sol-execbench-b200-kernels): CUDA C++, CuTe DSL and Triton kernels, locally validated on B200. Scores are estimates, not confirmed leaderboard results.
- [**KernelIndex**](https://github.com/SamMausberg/KernelIndex): GPU performance index with source and benchmark provenance. Imported results are labeled reported until reproduced by the index.
- [**Command A+ vLLM benchmarks**](https://github.com/SamMausberg/capp-vllm-bench): Serving on two H100s: prefill, decode, KV cache, CUDA graphs and tuning, with raw logs.
- [**H100 serving estimator**](https://github.com/SamMausberg/h100-serving-estimator): GPU-seconds/request estimates from 91 Command A+ runs. Held-out evaluation; a simpler baseline wins on the unseen serving configuration.
- [**SmolLM2 CPU conformance**](https://github.com/SamMausberg/smollm2-cpu-conformance): 48 CPU numerical cases comparing full-sequence and KV-cache implementations with Transformers, for one model revision.
- [**Tensor parallel reference**](https://github.com/SamMausberg/tensor-parallel-reference): CPU decoder across 1, 2 and 4 processes, with numerical checks, wire accounting and 96 fault-injection cases.
