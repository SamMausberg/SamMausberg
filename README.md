# Sam Mausberg

GPU systems engineer focused on LLM inference, CUDA kernels and compilers. Based in Vancouver.

[Email](mailto:samuelmausberg@gmail.com) · [LinkedIn](https://www.linkedin.com/in/sam-mausberg/)

I'm building [FindTensor](https://findtensor.com), an experimental compiler and runtime for LLM inference in Rust, C++ and Python. Previously, I worked with Tor Aamodt at UBC on GPU architecture simulation.

## Open source

I've contributed code and bug reports to [FlashInfer](https://github.com/flashinfer-ai/flashinfer). My SM120 dispatch diagnostics and configuration API were [incorporated upstream](https://github.com/flashinfer-ai/flashinfer/pull/4802). I also reported and reproduced an [FP8 KV calibration bug](https://github.com/flashinfer-ai/flashinfer/pull/4984) that was fixed upstream.

Open PRs cover [Hopper MLA decode](https://github.com/flashinfer-ai/flashinfer/pull/4906), [FP8 prefill](https://github.com/flashinfer-ai/flashinfer/pull/4977), [attention output transforms](https://github.com/flashinfer-ai/flashinfer/pull/5098) and [ALiBi for tensor parallelism](https://github.com/flashinfer-ai/flashinfer/pull/5101).

## Selected projects

- **[B200 kernels](https://github.com/SamMausberg/sol-execbench-b200-kernels)**: CUDA C++ and CuTe kernels for NVIDIA SOL-ExecBench, with source and validation reports.
- **[KernelIndex](https://github.com/SamMausberg/KernelIndex)**: A GPU benchmark index that compares matching workloads and links each result to its source.
- **[H100 serving estimator](https://github.com/SamMausberg/h100-serving-estimator)**: GPU time per request modeled from 91 published vLLM runs on two H100s, with held-out evaluation.
- **[SmolLM2 conformance](https://github.com/SamMausberg/smollm2-cpu-conformance)**: CPU implementations of full-sequence and KV-cache inference, with 48 numerical conformance cases.
- **[Tensor parallel reference](https://github.com/SamMausberg/tensor-parallel-reference)**: A CPU decoder block across 1, 2 and 4 worker processes, with numerical checks and 96 fault-injection cases.
