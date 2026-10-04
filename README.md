# Sam Mausberg

I'm based in Vancouver, where I work on GPU systems and compilers for language models. I'm building [FindTensor](https://findtensor.com), an experimental compiler and runtime. Previously, I worked with Tor Aamodt at UBC on GPU architecture simulation.

[Email](mailto:samuelmausberg@gmail.com) · [LinkedIn](https://www.linkedin.com/in/sam-mausberg/)

## Research

Manuscripts, with code and supporting material:

- [The Work a Verifier Needs](https://github.com/SamMausberg/verified-progress) — token verification in language models.
- [A reachable-state separation between attention compression and its certificates](https://github.com/SamMausberg/attention-reachable-public-replay)
- [SQ learning and dimension complexity](https://github.com/SamMausberg/sq-dimension-research)
- [Memory return in quantum machines](https://github.com/SamMausberg/returning-constructor)

I also study [Erdős problems in Lean](https://github.com/SamMausberg/lean-formalizations).

## Upstream contributions

- **FlashInfer**: A [MoE routing fix](https://github.com/flashinfer-ai/flashinfer/pull/5451) was merged, and my [dispatch diagnostics and configuration API](https://github.com/flashinfer-ai/flashinfer/pull/4802) were incorporated upstream. I also reported and reproduced an [FP8 calibration bug](https://github.com/flashinfer-ai/flashinfer/pull/4984) that was fixed.
- **NVIDIA CCCL / CUB**: Merged changes to [DeviceMergeSort](https://github.com/NVIDIA/cccl/pull/11587), [DeviceMerge](https://github.com/NVIDIA/cccl/pull/11589) and [DeviceMemcpy](https://github.com/NVIDIA/cccl/pull/11590).
- **Accel-Sim**: Merged [container update for Ubuntu 24.04 and CUDA 13.1](https://github.com/accel-sim/Dockerfile/pull/11).

<details>
<summary>Other contributions and proposals</summary>

- Further [FlashInfer](https://github.com/flashinfer-ai/flashinfer/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg) and [CUB / Thrust](https://github.com/NVIDIA/cccl/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg) changes under review.
- **SGLang**: [Verification](https://github.com/sgl-project/sglang/pull/42209), [planning](https://github.com/sgl-project/sglang/pull/42195) and [serving fixes](https://github.com/sgl-project/sglang/pulls?q=is%3Apr+is%3Aopen+author%3ASamMausberg), under review.
- [GPU MODE QR benchmark checks](https://github.com/gpu-mode/reference-kernels/pull/170) and [torchcomms extension packaging](https://github.com/meta-pytorch/torchcomms/pull/3688), under review.
- [Accel-Sim application compatibility](https://github.com/accel-sim/gpu-app-collection/pull/85), under review.
- [Triton FP8 dot product](https://github.com/triton-lang/triton/pull/11386) and [GPGPU-Sim CUDA 13](https://github.com/accel-sim/gpgpu-sim_distribution/pull/134) proposals, closed without merge.

</details>

## Systems and tools

- [CAIRN](https://github.com/SamMausberg/cairn) — experimental language for CPU and GPU programs, designed for AI agents.
- [KernelIndex](https://github.com/SamMausberg/KernelIndex) — an index of GPU performance measurements.
- [B200 kernels](https://github.com/SamMausberg/sol-execbench-b200-kernels) — CUDA C++, CuTe DSL and Triton implementations.
- [Command A+ benchmarks](https://github.com/SamMausberg/capp-vllm-bench) — vLLM serving measurements on two H100s.
- [H100 serving estimator](https://github.com/SamMausberg/h100-serving-estimator) — estimates GPU time per request from 91 benchmark runs.
- [SmolLM2 CPU checks](https://github.com/SamMausberg/smollm2-cpu-conformance) — numerical comparisons with Transformers.
- [Tensor parallel reference](https://github.com/SamMausberg/tensor-parallel-reference) — a CPU implementation for studying execution across processes.