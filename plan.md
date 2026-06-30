# Kylin NGCC Submission Completion Plan

## 1. 当前目标

项目当前目标是**完成 Kylin 的 NGCC 提交质量收敛**，重点不再是历史整理，而是把现有包提升到可提交、可解释、可复现的状态。

当前实现布局如下：

- 主提交实现（`q=2^64`）：`Kylin-128`、`Kylin-256`、`Kylin-512`
- Additional 源码实现（`q=2^24`）：`Kylin-128-q24`、`Kylin-256-q24`、`Kylin-512-q24`，当前源码树位于 `Implementations/Additional_Implementation/{Reference_Implementation,Optimized_Implementation}/`；最终打包时采用扁平的 `Additional_Implementation/Kylin-*-q24` 结构。

参数定版文件：`paper/data/para_kylin_final_6profiles.csv`。

历史归档目录已从当前提交包中移除，不再作为本仓库材料维护。

最终电子提交包目标：新建仓库根目录 `build/` 作为暂存区，按 `docs/公钥密码算法提交要求.md` 组织材料，并在 `build/` 内生成日期命名的 `Kylin-{mmdd}.zip`，例如 `Kylin-0429.zip`。

## 2. 已有基础（已完成）

- 当前三组基线实例（128/256/512）的参考实现与优化实现目录已建立；`q=2^24` 三组已作为 Additional 源码实现维护，并在最终提交包中按扁平 Additional 布局打包；六组最终参数已导出并冻结。
- NGCC SIG API 封装、KAT 生成链路、顶层自动化构建流程已可运行。
- 文档已移除历史家族对比内容，主叙事聚焦 Kylin 提交包。
- `make verify` 与论文多轮编译流程已通过，主文档引用已修复。

## 3. 工作流与阶段规划

### Phase A: 参数优化与定版（Priority: P0, Status: Done）

**目标**：在 NGCC 约束下完成六组参数搜索、对比与定版，并冻结后续口径。

任务（已完成）：

- 完成 `q in {2^64, 2^24}` 与 `sec in {128,256,512}` 的六组参数搜索。
- 明确并应用约束口径，生成候选明细与位次图，完成复核。
- 固化最终参数文件 `paper/data/para_kylin_final_6profiles.csv`。
- 将 `h_vec` 统一规范为升序输出，保持结果一致可复现。

验收标准（已满足）：

- 参数脚本可一键复现实验结论，并产出六组最终参数。
- 六组参数在汇总文件中固定，后续文档与实现对齐该文件。
- 参数优化阶段结项，除非明确提出新约束，不再变更参数。

### Phase B: 代码优化与工程质量（Priority: P0）

**目标**：提升 64-bit PC 优化实现质量，确保稳定、可维护、可比较。

任务：

- 对关键路径（`thash`/WOTS/FORS/树遍历）做 profiling 与热点定位。
- 在不破坏 API/KAT 兼容性的前提下做局部优化。
- 完整补齐自测矩阵：正确签验、篡改失败、错误公钥失败、长度接口一致性。
- 统一 benchmark 与内存统计脚本输出格式，减少手工步骤。

验收标准：

- 优化实现相较参考实现在核心指标有可量化提升。
- `make verify` 持续通过。
- KAT 结果保持稳定且可复现。

### Phase C: 文档完善（英文定稿 + 中文双轨文档）（Priority: P1）

**目标**：输出完整、提交导向、可长期维护的中英文材料，其中英文稿是唯一事实源，中文稿是可独立编译的同步翻译版。

任务：

- 英文文档统一术语与命名（全部聚焦 Kylin/NGCC），并继续作为唯一事实源。
- 抽取共享 LaTeX 骨架，保持英文入口 `main.tex`，新增中文入口 `main_zh.tex`，目标产物为 `main_zh.pdf`。
- 建立中文镜像章节/片段维护方式：自然语言内容分别维护，中英文共用公式、CSV 数据、参考文献、代码片段与标签语义。
- 按“全文翻译”范围补齐中文稿，并将目录、图、表、算法、定理类标题和引用名称做成全中文界面。
- 固化术语表与 EN->ZH 同步指引，明确哪些内容必须翻译、哪些内容绝不翻译，以及英文章节变动后的同步流程。
- 在构建链中增加中文文档命令，并把 XeLaTeX、中文 TeX 宏包、中文字体等依赖要求写入仓库说明；依赖通过环境安装提供，不直接 vendor 到仓库。
- 保证图表、表格、引用、术语、参数、实例名和公式在中英文间一致。

验收标准：

- 英文文档可直接用于提交包，并继续稳定生成 `main.pdf`。
- 中文文档可独立编译生成 `main_zh.pdf`，且覆盖当前英文主文档的完整内容。
- 中文 PDF 使用全中文界面标签，交叉引用、目录、参考文献和代码片段渲染正常。
- 中英文在表格数值、参数、实例名、公式与引用语义上保持一致。
- 术语表与 EN->ZH 同步指引足以支持后续反复同步英文改动。

### Phase D: 提交打包与清单收口（Priority: P0）

**目标**：形成可直接交付的 NGCC 提交目录与检查清单。

任务：

- 新建或刷新仓库根目录 `build/`，只把待提交材料复制到该暂存目录。
- 编译当前英文算法文本 `main.pdf`，并复制到 `build/算法文本.pdf`。
- 在 `build/` 根目录放置 `算法基本信息.pdf` 与 `知识产权声明.pdf`；二者应是签字扫描 PDF，若尚未取得则在 checklist 中标为人工阻塞项。
- 复制 `Test_Vectors/` 到 `build/Test_Vectors/`，保留所有 KAT 文件。
- 复制 `Implementations/` 到 `build/Implementations/` 时只保留提交所需结构：`Reference_Implementation/`、`Optimized_Implementation/`、`Additional_Implementation/` 和 `README`。
- 主提交三档 `Kylin-128`、`Kylin-256`、`Kylin-512` 保留在 `build/Implementations/Reference_Implementation/` 与 `build/Implementations/Optimized_Implementation/`。
- 将源码树中的 `Implementations/Additional_Implementation/Optimized_Implementation/Kylin-*-q24` 提升为最终包内的 `build/Implementations/Additional_Implementation/Kylin-*-q24`，不要在最终包中保留嵌套的 `Additional_Implementation/Optimized_Implementation/` 层级。
- 重写 `build/Implementations/README`，使其只描述最终打包树、每个 shipped 文件/目录的职责，以及 q24 Additional 的扁平布局。
- 从 `build/` 内打包生成 `Kylin-{mmdd}.zip`，其中 `{mmdd}` 使用打包当天月日，例如 `Kylin-0429.zip`。
- 默认打包烟测覆盖主提交 `Kylin-128/256/512` 的参考实现与优化实现；`Kylin-*-q24` 的 `make test` 单次可能需要 10 分钟以上，除非明确要求，否则不纳入默认打包烟测。
- 生成提交前 checklist（接口、文件完整性、可重复构建、版本标识、签字 PDF 状态、q24 测试是否显式执行）。

验收标准：

- 从干净环境可复现构建与主要验证流程。
- 提交包根目录包含 `算法基本信息.pdf`、`算法文本.pdf`、`知识产权声明.pdf`、`Implementations/`、`Test_Vectors/`。
- `build/Implementations/` 只包含提交所需实现目录与重写后的 `README`；Additional q24 实例以 `Additional_Implementation/Kylin-*-q24` 的扁平结构出现。
- zip 文件命名与打包日期一致，例如 4 月 29 日打包为 `Kylin-0429.zip`。
- checklist 全项有状态，阻塞项明确。

## 4. 执行原则

- 每个中等规模任务完成后：更新 `plan.md` 进度日志，并执行 `git add`、`git commit`、`git push`。
- 默认优先读取 `Implementations/`、`docs/`、`paper/`、`main.tex`；历史归档目录已移除，不再作为读取来源。
- 任何参数变更必须同步：实现常量、文档表格、测试向量、说明文字。
- 任何影响英文文档结构或自然语言内容的任务，都要同步评估中文镜像章节、术语表和 EN->ZH 同步指引是否需要更新。

## 5. 进度日志

### 2026-06-24 - Clean Submission Worktree State (Done)

- 将根目录受管的 `算法文本.pdf` 刷新为当前英文 `main.pdf` 内容，避免继续保留旧 42 页算法文本或删除状态；当前根目录算法文本与本次打包使用的 `build/算法文本.pdf` 同源。
- 纳入当前 11 页 `知识产权声明.pdf` 以及 BPORS 迁移来源材料 `new-files/Shorter Hash-based Signatures via Bucket Thinning.pdf` 与 `new-files/Shorter_Hash-based_Signatures_via_Bucket_Thinning.md`，使先前未跟踪/未提交的提交材料和迁移依据进入版本管理。
- 将根目录生成物 `main.pdf` 加入 `.gitignore`，保留本地构建产物但不再让它污染工作区状态。
- 验证：`算法文本.pdf` 与当前 `main.pdf` 的 SHA-256 一致；`pdftotext 算法文本.pdf` 可检出 Abri--Katz ePrint 2025/2069 引用；`git diff --check` 通过。

### 2026-06-24 - Rebuild Electronic Package After Citation Update (Done)

- 重新构建英文算法文本：`make -C paper/build all` 通过，并将最新 `main.pdf` 复制为 `build/算法文本.pdf`；包内算法文本已包含 Abri--Katz ePrint 2025/2069 引用。
- 重建 fresh `build/` 电子提交树，根目录包含 `算法基本信息.pdf`、`算法文本.pdf`、`知识产权声明.pdf`、`Implementations/` 与 `Test_Vectors/`；主提交 Ref/Opt 六个实例保留在对应目录，q24 companion 从 `Additional_Implementation/Optimized_Implementation/Kylin-*-q24` 提升为扁平 `Additional_Implementation/Kylin-*-q24`。
- 重写包内 `build/Implementations/README`，并清理包内 Makefile，使其只依赖随包源码并提供 `all/test/kat/clean` 目标，不引用仓库本地 `tools/`、benchmark 或 stack-usage 目标。
- 生成 `build/Kylin-0624.zip`，大小约 7.8 MB，SHA-256 为 `2abbed7d13a2b965bc8e29aac99e2538e6398d74b95187489ebeb7d26550e32d`。
- 验证：源树主提交 Ref/Opt 六个 q64 实例 `make clean all test` 通过；包内主提交 Ref/Opt 六个 q64 实例 `make clean all test` 通过；包内 q24 Additional 三个实例 `make clean all` 通过，q24 `make test` 仍按默认打包策略跳过；六个 KAT 文件均为 120 行且与仓库根 `Test_Vectors/` 逐字节一致；zip 清单为 321 项，不含 `tools/`、`benchmarks/`、`output/`、`.stack-usage/`、对象文件、栈报告、生成可执行文件或嵌套 Additional 实现层级。

### 2026-06-24 - Cite Forced-Pruning Hash-Signature Work (Done)

- 在英文主文档的无状态哈希签名相关工作、设计差异、BPORS+FP 构造说明、设计依据与安全性证明入口处引用 Abri--Katz 的 ePrint 2025/2069 `Shorter Hash-Based Signatures Using Forced Pruning`，使用现有 CryptoBib key `EPRINT:AbrKat25`。
- 同步中文镜像章节，补齐 `paper/tex-zh/construction.tex` 中对 BPORS+FP 与超树分层高度两项改进的概述，使其与英文构造概览保持一致。
- 验证：`make -C paper/build all` 与 `make -C paper/build zh` 均通过；日志未发现未解析 citation/reference 或 LaTeX error，剩余为既有 overfull/underfull 与中文字体 fallback warning。

### 2026-06-24 - Retune BPORS Parameters and Regenerate KATs (Done)

- 将 Kylin 的底层少次签名层迁移后的参数重新搜索并冻结到 `paper/data/para_kylin_final_6profiles.csv`；新增 `paper/code/search_bpors_kylin_params.py` 作为 BPORS+FP-aware 复现实验脚本，并保留旧 FORS baseline 到 `paper/data/para_fors_baseline_6profiles.csv` 作为 105% sign/verify hash-call cap 的比较源。
- 最终主提交参数为：`Kylin-128` 6472 字节，`Kylin-256` 25352 字节，`Kylin-512` 91528 字节；q24 companion 参数为：`Kylin-128-q24` 3064 字节，`Kylin-256-q24` 13256 字节，`Kylin-512-q24` 38984 字节。q24 搜索加入 practical forced-pruning floor `tau>=5e-7`，避免 KAT 生成落入上亿次 counter trial 的不可交付区间。
- 同步 12 个实现目录的 `params.h`，修复 q24 `Makefile` KAT 输出路径，并修复 `Implementations/tools/collect_metrics.py` 对嵌套 q24 Reference/Optimized 目录的发现与 impl 标注。
- 清理英文和中文构造章节中的旧 FORS 活跃内容，更新 BPORS+FP 地址说明、参数表、concrete security 表、hash-call performance 表、q24 appendix、test-vector SHA-256 表、`Implementations/README`、术语表、EN->ZH 同步指南，并新增 `docs/bpors-retune-impact.md`。
- 验证：`python3 paper/code/check_bpors_profiles.py` 通过；主 q64 Ref/Opt 六组 `make test` 通过；q24 Ref/Opt 六组 `make test` 通过；六个 profile 的 KAT 文件已重新生成到 `Test_Vectors/`，每个 120 行并记录 SHA-256；主 q64 package benchmark/memory 通过 `python3 Implementations/tools/collect_metrics.py` 刷新。

### 2026-06-23 - Integrate Security Proof Into Main Paper (Done)

- 将 `new-files/kylin_security_proof.tex` 的核心证明内容并入英文主文档 `paper/tex/security_statements_and_analyses.tex`，把原先简短安全声明扩展为完整安全性章节。
- 新增并整理安全模型与符号、\WOTSCS\ 常和反链引理、CS-WOTS-TW 单实例 game proof、多实例 theorem、Kylin EUF-CMA 归约 theorem、HT proof-oriented 描述、concrete generic attack section，以及与 H\"ulsing--Kudinov 紧致 \SPHINCSP\ 证明的关系说明。
- 统一证明符号口径：`n` 保持为字节安全参数，`N=8n` 表示比特长度；多实例数量使用 `D`，避免与超树层数 `d` 冲突；用本地 `\THFColl` 表示可调哈希函数族，避免嵌套已有 `\Th` 宏导致 LaTeX 条件分支错误。
- concrete section 继续以 `paper/data/para_kylin_final_6profiles.csv` 为冻结参数源，并明确列出 classical 与 quantum generic bit-security proxy；其中 `Kylin-128` 的 generic quantum proxy 为 `63.605`，作为后续安全口径人工决策点保留。
- 同步中文镜像 `paper/tex-zh/security_statements_and_analyses.tex`，补充 `docs/en-zh-glossary.md` 与 `docs/en-zh-sync-guide.md` 中的安全证明维护术语和流程；为 `main_zh.tex` 增加 CJK 字体 fallback，使缺少 Noto CJK 的环境可继续构建中文 PDF。
- 验证：`make -C paper/build all` 通过并生成 46 页 `main.pdf`；`make -C paper/build zh` 通过并生成 54 页 `main_zh.pdf`。日志无 undefined references/citations 或 LaTeX errors；剩余 overfull/underfull 为既有排版项或小幅中文换行项。

### 2026-06-23 - Recheck English Paper Consistency (Done)

- 重新检查 `main.tex` 实际输入的英文论文源，重点覆盖 `paper/tex/kylin.tex`、`paper/tex/security_statements_and_analyses.tex`、`paper/tex/design_rationale.tex` 与 `paper/tex/kylin-appendix.tex`。
- 修正主文档中 `n` 为字节参数但 \WOTSCS\ 编码空间仍写作 `2^n` 的两处残留，统一改为 `2^{8n}`；同时修正全签名格式描述中误用 HT 签名符号 `\sight` 和 `k(a+1)n`-byte strings 的易误读表述。
- 修正 appendix 中 `paper/code/para.sage` 的旧版 `Kylin-512` 参数，使其与冻结参数表一致：`h=66,d=11,h_vec=[6,...,6],a=13,k=49,w=97,len=79`；`python3 paper/code/para.sage` 现已通过漂移断言。
- 同步备用 `paper/tex/submission_overview.tex` 中旧的 `h\in\{65,68,70\}`，并修正 `q=2^{24}` appendix 标题的 PDF bookmark 写法，消除 hyperref 书签 warning。
- 验证：`python3 paper/code/search_ngcc_params.py` 输出冻结三档参数；`make -C paper/build all` 通过并生成最新 `main.pdf`；源码/PDF 扫描未发现旧 `2^n`、旧 `h=70`、`65,68,70` 或断引用 `??`。
- 待人工决策：当前脚本仍明确输出 `Kylin-128` 的 `formula_quantum=63.6`，而 NGCC 等级标签为 `128/80`；这不是排版或同步问题，若要把 generic quantum exponent 也作为强声明，需要重新确认安全口径或重选参数。

### 2026-06-23 - Refresh Kylin Security Proof Draft (Done)

- 聚焦 `new-files/kylin_security_proof.tex`，修正安全证明草稿中的符号口径：`n` 统一为 Kylin 字节安全参数，新增 `N=8n` 表示位长，并清理旧的 `\bits^n`、`2^n` 写法。
- 收紧 CS-WOTS+ 证明部分：将最大反链论证改为对 `[w]^\ell` 的对称链分解证明，并说明编码消息空间与 `D_{\ell,\lfloor \ell(w-1)/2\rfloor}\ge 2^N` 的关系。
- 修正 HT 描述：按底层到顶层给出非均匀高度 hypertree 的树数量公式，明确 HT 每层签名只包含一个 CS-WOTS-TW 签名和 `h_i` 个认证路径节点，FORS 的 `a=\log t` 认证节点仅属于 `\sigma_{\mathsf{FORS}}`。
- 恢复并重写 concrete security section，使 `sec:concrete` 成为可引用章节；公式与 `paper/code/search_ngcc_params.py` 使用的 generic attack proxy 对齐，并列出六组冻结 profile 的 classical exponent。
- 验证：`pdflatex -interaction=nonstopmode kylin_security_proof.tex` 多轮通过并生成更新后的 `new-files/kylin_security_proof.pdf`；日志无 warning/overfull；PDF 文本扫描无断引用 `??`；源码扫描确认无残留 `\bits^n` 或 `2^n`。

### 2026-04-30 - Refresh Final NGCC Submission Zip (Done)

- 重新编译当前英文算法文本，生成最新 `main.pdf`，并复制到新的 `build/算法文本.pdf`；同时将当前仓库中的 `算法基本信息.pdf`、`知识产权声明.pdf` 与 `Test_Vectors/` 一并纳入本次提交暂存区。
- 重建全新的仓库根目录 `build/`，按最终提交树复制 `Implementations/`：保留主提交 `Reference_Implementation/Kylin-{128,256,512}` 与 `Optimized_Implementation/Kylin-{128,256,512}`，并继续将 `Implementations/Additional_Implementation/Optimized_Implementation/Kylin-*-q24` 提升为扁平的 `build/Implementations/Additional_Implementation/Kylin-*-q24`。
- 重写 `build/Implementations/README`，使其只描述实际 shipped 的提交树、参数、通用源文件清单，以及扁平 q24 Additional 布局；继续排除仓库开发态的 `tools/`、`benchmarks/`、嵌套 Additional staging 树、生成的可执行文件、`output/` 与 `.stack-usage/`。
- 从 `build/` 内打包生成 `build/Kylin-0430.zip`，并用 `unzip -l` 复核压缩包根目录材料、Additional 扁平结构和 `Test_Vectors/` 内容。
- 验证：`make -C paper/build all` 通过；主提交 `Kylin-128/256/512` 的 Ref/Opt 六个实例均完成 `make clean all test`；`q24` 版本按本次明确要求未做测试，仅打包其提交源码与现有 KAT 文件。

### 2026-04-29 - Build Final NGCC Submission Zip (Done)

- 编译英文算法文本并将最新 `main.pdf` 复制为 `build/算法文本.pdf`，同时复制 `算法基本信息.pdf`、`知识产权声明.pdf` 与 `Test_Vectors/`。
- 构造最终 `build/Implementations/`：保留主提交 `Reference_Implementation/Kylin-{128,256,512}` 与 `Optimized_Implementation/Kylin-{128,256,512}`，并将 q24 优化实现提升为 `Additional_Implementation/Kylin-*-q24`。
- 在最终包内重写 `Implementations/README`，描述实际 shipped 目录、实例、参数、通用源文件与构建方式。
- 打包生成 `build/Kylin-0429.zip`；结构检查确认包内无生成的可执行文件、`output/`、`.stack-usage/`、`tools/` 或 `benchmarks/`，且 Additional q24 没有嵌套实现层级。
- 验证：`make -C paper/build all` 通过；最终包内主提交 Ref/Opt 的 `Kylin-128/256/512` 均完成 `make clean all test`；q24 test 默认跳过（`Kylin-128-q24` 曾误启动并自然完成，`Kylin-256-q24` 与 `Kylin-512-q24` 未运行）。

### 2026-04-29 - Final NGCC Packaging Rules Captured (Done)

- 将最终电子提交包的暂存方式固定为仓库根目录 `build/`，并明确从 `build/` 内生成 `Kylin-{mmdd}.zip`。
- 固定包根目录材料：`算法基本信息.pdf`、由当前 `main.pdf` 编译后改名得到的 `算法文本.pdf`、`知识产权声明.pdf`、`Implementations/` 与 `Test_Vectors/`。
- 固定 `build/Implementations/` 的提交结构：保留主提交 `Reference_Implementation/` 与 `Optimized_Implementation/`，将源码树中 `Additional_Implementation/Optimized_Implementation/Kylin-*-q24` 提升为最终包内扁平的 `Additional_Implementation/Kylin-*-q24`。
- 明确最终包内需要重写 `Implementations/README`，使其描述实际打包结构和 shipped 文件，而不是仓库本地 benchmark/tooling 布局。
- 补充 q24 验证策略：`Kylin-*-q24` 的 `make test` 单次可能需要 10 分钟以上，默认打包烟测不运行 q24 test，除非后续明确要求。

### 2026-04-27 - Clean Tracked Generated Files (Done)

- 统计当前仓库文件：清理前 Git 受管文件为 631 个，工作区排除 `.git` 后为 726 个文件。
- 从 Git 中移除 6 个 `bench_sig_1iter` ELF 可执行产物和 3 个 `paper/code/__pycache__/*.pyc` Python 缓存文件；清理后 Git 受管文件为 622 个。
- 补充 `.gitignore`：忽略 `Implementations/**/bench_sig_1iter`、`__pycache__/`、`*.py[cod]` 以及中文 LaTeX 的 `main_zh.bbl`/`main_zh.blg` 生成物。
- 验证：受管文件中不再包含 `bench_sig_1iter`、`__pycache__` 或 `.pyc` 产物。

### 2026-04-27 - Merge Second Overleaf PR Conservatively (Done)

- 处理远端分支 `overleaf-2026-04-27-0441`：该分支同样来自较早 Overleaf 同步轨道，会删除当前 Kylin NGCC 实现、中文文档、数据文件与维护记录，并把论文入口回退到旧 SPHINCS-alpha 结构。
- 继续采用 `ours` merge 策略将该 PR 作为已合并历史记录到 `main`，同时保留当前 Kylin/NGCC 文件树。
- 验证：合并后没有引入 PR 的破坏性文件树变更；仅本计划记录发生内容变化。

### 2026-04-27 - Merge Overleaf PR Conservatively (Done)

- 处理远端分支 `overleaf-2026-04-27-0433`：该分支来自较早基点，Overleaf 同步内容会删除当前 Kylin NGCC 提交包中的实现、中文文档、数据文件与维护记录，并回退到旧 SPHINCS-alpha 文档轨道。
- 采用 `ours` merge 策略将该 PR 作为已合并历史记录到 `main`，同时保留当前 Kylin/NGCC 文件树与刚完成的归档目录清理结果。
- 验证：合并后没有引入 PR 的破坏性文件树变更；仅本计划记录发生内容变化。

### 2026-04-27 - Remove Historical Archive Directory (Done)

- 按清理请求删除历史归档目录，当前提交包只保留 Kylin NGCC 相关实现、文档、数据与构建材料。
- 同步更新 `AGENTS.md` 与本计划中的归档目录说明，避免继续把已删除目录描述为可用材料。
- 验证：目录已不存在；剩余受管文本中不再引用该历史归档路径。

### 2026-04-27 - Sync q24 Package Benchmarks into Appendix B (Done)

- 将 `paper/data/package_bench.csv` 中三组 `Kylin-*-q24` 的最新 Ref/Opt package benchmark 数据同步到英文 Appendix B 的 `q=2^24` 基准表。
- 在中文镜像附录 B 中新增对应的 `q=2^24` 基准表与优化实现说明，使中英文附录的结构、数值和引用语义保持一致。
- 验证：`make -C paper/build all` 与 `make -C paper/build zh` 均通过并刷新 `main.pdf`、`main_zh.pdf`；仅保留既有的局部 overfull 与 appendix `hyperref` 提示。

### 2026-04-27 - Implementation README File Inventory Completion (Done)

- 按 NGCC 提交要求补全 `Implementations/README`：新增顶层文件清单、三类实现目录清单、每个实例目录的通用文件清单与逐文件职责说明。
- 明确 `Additional_Implementation/Kylin-128-q24/timing_probe` 为额外保留的本地计时探针，并说明 `KAT_SIG`、`test_sig`、`bench_sig`、`output/`、`.stack-usage/` 属于生成物，不作为源文件清单的一部分。
- 验证：`git diff --check` 通过。

### 2026-04-26 - Optimized Implementation Performance Rerun without Additional Profiles (Done)

- 按 `Optimized_Implementation` 最新代码重新执行主提交三档 `Kylin-128/256/512` 的 Ref/Opt package benchmark 与 stack/code-size 统计，不测量 reference-only Additional `q=2^24` 实例。
- 刷新 `paper/data/package_bench.csv`、`paper/data/package_memory.csv` 与 `Implementations/benchmarks/summary.md`。本轮主表仍仅包含三组主提交实例的 Ref/Opt 六行。
- 将 `Implementations/tools/collect_metrics.py` 的默认收集范围收紧为主提交 Ref/Opt，并新增 `--include-additional` 作为显式开关；同步更新 `Implementations/README`。
- 同步更新英文 `paper/tex/performance_evaluation.tex` 与中文镜像 `paper/tex-zh/performance_evaluation.tex` 中的实测加速比结论。
- 验证：三组优化实现 `make test` 通过；`make metrics` 通过；`make -C paper/build all` 与 `make -C paper/build zh` 通过，仍仅有既有的 overfull/underfull 与 appendix `hyperref` 提示。

### 2026-04-26 - Primary Benchmark Refresh after Optimized Implementation Update (Done)

- 在 `Optimized_Implementation` 更新后，重新执行 `Kylin-128/256/512` 三个主提交优化实现的 `make test`，确认签名/验签流程仍正常。
- 重新测试六个主提交实例（Ref/Opt）的 package benchmark，刷新 `paper/data/package_bench.csv`，并同步更新英文 `Performance Evaluation` 与中文对应章节中的平台说明、测试方法和加速比结论。
- 修复 `Implementations/Optimized_Implementation/Kylin-128/Makefile` 的 `stack_usage` 统计路径：在该目标下去掉 `-flto`，避免 `.su` 文件缺失并纠正此前偏低的栈使用结果。
- 基于同一批次测量刷新 `paper/data/package_memory.csv` 与 `Implementations/benchmarks/summary.md`，使论文数据、仓库指标摘要和内存统计保持一致。
- 构建验证：`make -C paper/build all` 与 `make -C paper/build zh` 通过；仍保留少量既有的 appendix `hyperref` 提示与局部 overfull box 告警。

### 2026-04-26 - Chinese Translation Track Initial Build (Done)

- 新增中文入口 `main_zh.tex`，并补齐 `paper/tex-zh/`、`paper/figure-zh/`、`paper/tex/defs_zh.tex` 作为当前英文主文档的完整中文镜像轨道。
- 为中文镜像章节与图表片段补充了源文件映射注释，降低后续 English -> Chinese 同步时的定位成本。
- 新增 `docs/en-zh-glossary.md` 与 `docs/en-zh-sync-guide.md`，固定术语、翻译边界、文件映射、构建命令与后续维护流程。
- 在 `paper/build/Makefile` 中加入 XeLaTeX 中文构建目标，在仓库根 `Makefile` 中加入便捷命令 `make paper-zh`。
- 构建验证：`make -C paper/build zh` 通过并生成 `main_zh.pdf`；`make -C paper/build all` 继续生成 `main.pdf`。中文构建当前仅剩 appendix 书签里的既有 `hyperref` 提示，英文字稿仍保留原有少量文档告警。

### 2026-04-26 - Chinese Document Track and EN->ZH Sync Policy Capture (Done)

- 明确中文文档方向以当前英文主文档为基准，采用“全文翻译”而不是局部翻译。
- 固定双语维护策略为“镜像章节 + 共享公式/数据/参考文献 + 术语表 + EN->ZH 同步指引”，英文稿继续作为唯一事实源。
- 固定本地化程度为“全中文界面”：目录、图、表、算法、定理类标题和引用名称都应中文化。
- 固定中文工具链策略为 XeLaTeX 路线，并将中文 TeX 宏包与中文字体作为环境依赖写入说明，而不是将第三方字体/宏包直接纳入仓库。
- 将上述长期规则写入 `AGENTS.md`，并将 Phase C 扩展为可执行的中文双轨文档建设计划。

### 2026-04-26 - NGCC 3.3 Specification Section Rewrite (Done)

- 按 `docs/Submission Requirements for Public-Key Cryptographic Algorithms.md` 中 3.3.2--3.3.5 的口径重写正文关键章节：
  - `Design Rationale` 补入数学困难问题、参数选择依据、失败/伪造概率影响分析，并明确 Diverse Layer Heights 优化；
  - `Security Statements and Analyses` 增加理论安全 TODO、具体安全/失败概率表、当前不声明的其他安全特性；
  - `Performance Evaluation` 增加 hash-call/signature-size 表、本机 64-bit PC 平台配置和软件性能/传输存储开销合表；
  - `Feature Statements` 按创新性、简洁性、灵活性、兼容性、可扩展性和平台实现优势重写。
- 文档结构调整：
  - `main.tex` 不再输入摘要、`Submission Package Overview`、`Basic Information`；
  - `Algorithm Description and Background` 改名为 `Algorithm Description`；
  - 冻结主参数表迁入算法规格正文，继续使用 `Kylin-128/256/512` 三组主提交实例。
- 修复 `\pk` / `\sk` 渲染：
  - 改为文本/数学双模式 robust 宏；
  - 将 hash-call 表改为手写冻结值，避免 CSV 表头 `pk`/`sk` 与正文宏再次冲突。
- 验证：
  - 编译验证：`latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error main.tex` 通过，并刷新 `main.pdf`。
  - PDF 文本抽查：TOC 中已无 `Abstract`、`Submission Package Overview`、`Basic Information`；正文中 `PK.seed` / `SK.seed` 可正常抽取。

### 2026-04-26 - Kylin-512 Re-selection under `sign_hashcalls < 6.4e6` (Done)

- 按新约束重新筛选主提交 `Kylin-512`：目标改为在 `sign_hashcalls < 6,400,000` 前提下最小化 `sig`。
- 更新搜索脚本口径：
  - `paper/code/search_kylin_six_profiles.py` 对 `Kylin-512` 放宽到 `w <= 128` 并按 `sign_hashcalls` 上限选点；
  - `paper/code/search_ngcc_params.py` 同步放宽 `W_CHOICES`，并将冻结 `Kylin-512` 主配置改写为新参数。
- 新冻结参数定为：
  - `Kylin-512`: `q=2^64, n=64, h=66, d=11, h_vec=[6,6,6,6,6,6,6,6,6,6,6], a=13, k=49, w=97, len=79`
- 对应指标：
  - `sig = 103808`
  - `sign_hashcalls = 6198272`
  - `verify_hashcalls = 42476`
  - `bitsec = 511.243016`
- 代码与文档同步范围：冻结 CSV、主/优实现 `params.h`、README/摘要等硬编码参数说明。
- 验证与产物同步：`Reference_Implementation/Kylin-512` 与 `Optimized_Implementation/Kylin-512` 的 `make test` 通过，新的 `Test_Vectors/KAT_SIG_Kylin-512.txt` 已生成并同步，`package_bench/package_memory/benchmarks summary` 已改写为新参数结果。

### 2026-04-24 - Plan Reset: NGCC Submission Focus

- 将计划主线切换为“完善 NGCC 提交”，不再使用历史整理导向结构。
- 重建四阶段路线图：参数优化、实现优化、文档完善、提交打包。
- 明确了每阶段任务清单与可验证验收标准。

### 2026-04-24 - Baseline Consolidation (Done)

- 现有三实例代码、KAT、自动化验证、文档去历史化与引用修复均已完成并通过当前检查流程。

### 2026-04-25 - Scope Update: Six-Profile Parameter Target

- 参数优化目标由三组基线扩展为六组提交配置：`{128,256,512} x {fast,small}`。
- 明确 `fast` 目标为“在合理范围内优先提升签名速度”，`small` 目标为“在合理范围内优先缩小签名尺寸”。
- 更新了 Phase A 任务与验收标准，以 six-profile 导出与一致性落地为核心。

### 2026-04-25 - Hypertree Per-Layer Height Refactor (All-7 Compatible)

- 将参考实现与优化实现的 `Kylin-{128,256,512}` 统一改造为“分层高度向量”模型：`(h_0,\dots,h_{d-1})`，并保持当前配置为 10 层全 `7`（总高仍为 `70`）。
- 代码侧已完成以下改造：参数定义、`hash_message` 的 `tree/leaf` 位拆分、`ht` 每层签名/验签索引推进、`merkle_sign` 层高参数化、地址字段约束同步。
- 文档侧已同步修改 `HT: The Hypertree`、`spa_sign/spa_verify` 与 `ht_sign/ht_verify` 伪代码、消息摘要长度公式与复杂度公式，去除统一 `h/d` 叙述。
- 验证结果：六个实现目录全部 `make clean all test` 通过；三组参考实现 `make kat` 通过，`Test_Vectors/` 无变更，确认“全 7”下输出行为保持不变。

### 2026-04-25 - Parameter Evaluation Script Rewrite for `{h_i}` (Done)

- 重写附录脚本 `paper/code/para.sage`：统一采用分层高度向量模型，核心约束为 `sum_i h_i = h`，并将摘要拆分与 HT hash-call 估计改为依赖 `h_0` 与 `sum_i 2^{h_i}`。
- 更新主参数搜索脚本 `paper/code/search_ngcc_params.py`：移除旧的“`d` 必须整除 `h`”假设，改为 `{h_i}` 语义下的层数候选与 profile 兼容性约束；CSV 输出补充 `h_profile/h0/digest_bytes` 字段用于追踪分层配置。
- 重新生成 `paper/data/para_ngcc.csv` 并执行“先用全 7 验证不变”回归：三档参数均保持 `h=70, d=10, h_vec=[7,...,7]`，`sig/hashcalls` 与既有基线一致。
- 测试与构建：`python3 paper/code/para.sage`、`python3 paper/code/search_ngcc_params.py --write-csv paper/data/para_ngcc.csv`、`make -C paper/build all` 全部通过。

### 2026-04-25 - SIG-HashCall Hull Refresh with New Search Ranges (Done)

- 按需求将 `paper/code/search_ngcc_params.py` 的搜索范围更新为：`W_CHOICES=range(8,88)`、`H_CHOICES=range(63,71)`、`A_CHOICES=range(8,17)`。
- 基于新范围重新进行参数枚举，并生成三张“仅下凸壳”图（分开绘制）：`Kylin-128/256/512` 的 `SIG(bytes)-hashcalls(proxy)` 曲线。
- 同步导出三份 hull 点集 CSV，便于后续复现实验和表格整理。
- 本轮统计：每个安全级别枚举候选 `846,000` 个；hull 点数分别为 `41`（128）、`54`（256）、`60`（512）。

### 2026-04-25 - Interactive SIG-HashCall Hull Viewer (Done)

- 新增脚本 `paper/code/generate_sig_hashcall_interactive.py`，按当前严格口径与搜索范围自动构建三档下凸壳点集，并输出纯 HTML 交互图。
- 输出文件 `paper/data/sig_hashcall_lower_hull_interactive.html`，支持鼠标悬停查看每个点的参数明细：`sig/hashcalls/h/d/h_vec/h0/a/k/w/len/classical_bitsec`。
- 该交互页不依赖 Python 绘图库，直接浏览器打开即可使用；当前统计与静态图一致（128/256/512 分别 29/35/49 个 hull 点）。

### 2026-04-25 - Re-search with `h >= 60` (Done)

- 按要求将参数搜索高度范围下界收紧为 `H_CHOICES=range(60,71)`，保持 `W=range(8,88)`、`A=range(8,17)` 不变。
- 基于新范围重算三档下凸壳，并覆盖更新三组静态图与点集 CSV，以及交互页面 `sig_hashcall_lower_hull_interactive.html`。
- 新统计（strict 口径）：候选数均为 `1,206,720`；hull 点数分别为 `44/57/63`（128/256/512）；对应最小签名为 `10560/29888/95488` 字节。

### 2026-04-25 - Replace Lower Hull with Pareto Step Frontier (Done)

- 根据需求将绘图边界从“几何下凸壳”改为“帕累托前沿（sig/hashcalls 双目标最小化）”，并使用阶梯折线展示离散取值边界。
- 新增静态生成脚本 `paper/code/generate_sig_hashcall_pareto_step.py`，可一键输出三档 `PNG/SVG/CSV`（CSV 含完整参数字段）。
- 改造交互脚本 `paper/code/generate_sig_hashcall_interactive.py`：前沿算法切换为 Pareto frontier，连线改为 step path，标题与统计字段同步调整。
- 在当前范围 `H=[60,70], A=[8,16], W=[8,87]` 下重算结果：前沿点数分别为 `163/285/410`（128/256/512），并生成新的交互页面。

### 2026-04-25 - Aggressive SIG-vs-Verify Parameter Experiment (Done)

- 新增实验脚本 `paper/code/generate_sig_verify_pareto_step.py`，目标函数切换为 `SIG(bytes)` 与 `verify_hashcalls(proxy)` 的 Pareto 前沿，`sign_hashcalls` 仅作参考列输出。
- 为避免低 `h` 区间数值失真，脚本默认限制 `h >= 60`；若仅做探索可显式传 `--allow-low-h` 强制放开。
- 验签 hash-call 代理采用实现导向计数：`FORS: k(a+1)+1`，`HT: d*(ceil(len*(w-1)/2)+1)+h`，并利用 `WOTSCS` 常和编码性质计算精确链步数。
- 按扩大范围运行实验（可信区间）：
  - `bitsec >= 127.5`：`h=[60,80], a=[6,30], w=[8,240]`，候选 `2,324,175`，前沿点 `25`，最小签名 `4912`，无 `sig < 4000`。
  - `bitsec >= 128.0`：同范围候选 `2,315,321`，前沿点 `25`，最小签名 `9248`，无 `sig < 4000`。
- 产物文件：
  - `paper/data/sig_verify_pareto_step_kylin128_target1275_wide_h60_80_a6_30_w8_240.{csv,png,svg}`
  - `paper/data/sig_verify_candidates_siglt4000_kylin128_target1275_wide_h60_80_a6_30_w8_240.csv`
  - `paper/data/sig_verify_pareto_step_kylin128_target1280_wide_h60_80_a6_30_w8_240.{csv,png,svg}`
  - `paper/data/sig_verify_candidates_siglt4000_kylin128_target1280_wide_h60_80_a6_30_w8_240.csv`

### 2026-04-25 - Extended Search with `h >= 54` and `bitsec >= 127.5` (Done)

- 按新增要求继续扩大搜索下界到 `h >= 54`，并保持验签目标函数：`SIG(bytes)` 对 `verify_hashcalls(proxy)` 的 Pareto 前沿。
- 为避免低 `h` 区间安全估计偏差，更新实验脚本中的 bit-security 计算为更宽支持区间的稳健分布求和（仅用于实验脚本，不影响主线脚本）。
- 运行范围：`h=[54,80], a=[6,30], w=[8,240]`；枚举候选 `2,939,528`，前沿点 `25`。
- 结果：最小签名仍为 `4912`，`sig < 4000` 仍无可行参数。
- 产物文件：
  - `paper/data/sig_verify_pareto_step_kylin128_target1275_wide_h54_80_a6_30_w8_240.{csv,png,svg}`
  - `paper/data/sig_verify_candidates_siglt4000_kylin128_target1275_wide_h54_80_a6_30_w8_240.csv`

### 2026-04-25 - Expanded Constraint Search with `h >= 50`, `d >= 4`, `bitsec >= 127.0` (Done)

- 按新约束继续扩张搜索，重点转为 `d=4` 极限方向（在 `d>=4` 下最小签名必由最小 `d` 给出），并保留扩张范围 `h=[50,80], a=[6,48], w=[8,320], k<=1200`。
- 输出 `SIG vs verify_hashcalls` Pareto 前沿及 `<4000` 筛选文件：
  - `paper/data/sig_verify_pareto_step_kylin128_target1270_xwide_h50_80_d4_only_a6_48_w8_320_k1200.{csv,png,svg}`
  - `paper/data/sig_verify_candidates_siglt4000_kylin128_target1270_xwide_h50_80_d4_only_a6_48_w8_320_k1200.csv`
- 结果：最小签名 `4240`（参数点 `h=67,d=4,a=42,k=3,w=275,len=17,classical=127.238449`），`sig<4000` 仍无可行解。

### 2026-04-25 - Verify-HashCall Minimization Attempt (`<800`) (Done)

- 目标切换为优先最小化 `verify_hashcalls`，安全约束保持 `bitsec >= 127.0`（`Kylin-128`）。
- 复用稳健安全估计后，确认关键下界量 `M = h + k(a+1)` 在 `h >= 50` 下最小可行为 `M_min = 193`（与此前 `len=15` 扫描结论一致，并补充了 `h>=81` 的 `M<=192` 不可行检查）。
- 在先前硬约束 `h>=50, d>=4, w>=8` 下，`verify_hashcalls` 理论与实测最小值为：
  - `verify_min = 1 + d*(steps_w+1) + M_min = 1 + 4*(158+1) + 193 = 830`
  - 达不到 `<800`。
- 若允许更激进参数，可进入 `<800`：
  - 保持 `d>=4`、将 `w` 放宽至 `2`：示例 `h=50,d=4,a=142,k=1,w=2,len=132`，`verify=462`，`sig=11552`，`bitsec=127.0`。
  - 进一步放宽到 `d=1,w=2`：示例 `h=50,d=1,a=142,k=1,w=2,len=132`，`verify=261`，`sig=5216`，`bitsec=127.0`。

### 2026-04-25 - Configurable Query Budget + Constrained Search (`q=2^24`, `h=20..25`, `sig<3800`) (Done)

- 更新 `paper/code/search_ngcc_params.py`：将查询预算 `q` 从硬编码改为可选 CLI 变量，新增 `--q-bits`（默认 `64`）与 `--q-sigs`；并在切换 `q` 时清理依赖缓存，避免复用旧分布结果。
- 新增约束搜索模式：`--search`、`--h-min/--h-max`、`--sig-max`、`--top`、`--write-search-csv`，可在给定约束下输出每档候选命中与明细。
- 按要求执行一次搜索：
  - `python3 paper/code/search_ngcc_params.py --search --q-bits 24 --h-min 20 --h-max 25 --sig-max 3800 --top 20 --write-search-csv paper/data/para_ngcc_search_q24_h20_25_siglt3800.csv`
  - 结果：`Kylin-128/256/512` 在该约束下均 `0` 命中（总计 `0`）。
- 回归检查（固定 shape 快速烟测）通过：`--h-min 70 --h-max 70 --shape 70 10 14 64` 仍可产出既有三档参数。

### 2026-04-25 - Keep External Baseline Parameter Sets in Code (Done)

- 在 `paper/code/search_ngcc_params.py` 新增 `BaselineParameter` 与常量 `BASELINE_PARAMETERS`，固化保留两组 baseline：
  - `q=2^64`: `sphincs-a-128s`, `sphincs-a-256s`
  - `q=2^24`: `SLH-DSA-SHAKE-128-24`, `SLH-DSA-SHAKE-256-24`
- 新增 baseline CLI 接口：
  - `--print-baselines`：直接打印当前代码中的 baseline。
  - `--write-baseline-csv <path>`：导出 baseline CSV。
- 验证命令：
  - `python3 paper/code/search_ngcc_params.py --print-baselines`
  - `python3 paper/code/search_ngcc_params.py --write-baseline-csv paper/data/para_baselines.csv`

### 2026-04-26 - Table 2/3 NGCC Draft Formatting Update (Done)

- 按提交口径更新 `Table 2`：移除 `q-bitsec` 展示列，`bitsec` 改为整数显示（`127/256/511`），并新增 `paper/data/para_ngcc_table_rounded.csv` 作为定稿表格数据源。
- 按提交口径重写 `Table 3`：取消与 `SPHINCS+` 的并列对比，仅展示 `Kylin-128/256/512` 三行指标；时间列统一改为 `Hashcall` 代理计数。
- 基于冻结参数补齐 `KeyGen Hashcall`，并整理为 `paper/data/kylin_hashcall_metrics.csv`；同时修复 `csvsimple` 下划线列名导致的 LaTeX 编译错误（列名改为无下划线）。
- 完成 `main.tex` 全量编译并通过，输出 PDF 已更新，表 2/表 3 显示符合当前提交需求。

### 2026-04-26 - Table 3 KeyGen Fix + Intro/Spec Text Cleanup (Done)

- 修正 `Table 3` 的 `KeyGen (Hashcall)` 口径：按正文“仅生成顶层 XMSS 树”的复杂度描述重算，使用顶层高度 `h_{d-1}` 计算，更新后分别为：
  - `Kylin-128`: `417279`
  - `Kylin-256`: `324095`
  - `Kylin-512`: `1482948607`
- 在 `Introduction` 的 `Stateless signatures` 段落前添加 TODO，标注后续补充 related work。
- 删除 `Other Changes Made` 段落中 “remove haraka and robust version ...” 句子。
- 在 `3 Kylin vs. SPHINCS+` 章节新增“Diverse Layer Heights in the Hypertree”小节，明确：
  - 不再要求 `h mod d = 0`；
  - 允许每层高度 `h_i` 不同且满足 `sum h_i = h`；
  - 令 `r = h mod d`，默认采用 `d-r` 个 `floor(h/d)` 与 `r` 个 `ceil(h/d)` 的平衡分配规则。
- 修复 `6.1.5 XMSS Signature` 与 `6.2.3 HT Signature` 中误用的 `*` 符号，统一改为 `\cdot` 形式，避免排版异常字符。
- 完成 `main.tex` 全量编译并通过，确认上述修改已在 PDF 中生效。

### 2026-04-26 - NGCC Hash-Instantiation Rewrite + q=2^24 Appendix (Done)

- 统一修复 `\len` 显示口径：宏定义改为稳定形式，并在 `paper/tex/kylin.tex` 内将 `\tt len` / 裸 `len` 的混用统一为 `\len`，避免章节内显示风格不一致。
- 重写 `9.2 Instantiations of Hash Functions`：从旧的 `SHA2/SHAKE` 叙述切换到 NGCC/ICCS 代码口径，明确使用 `sm3hash`、`pseudohash`、`pseudoXOF`，并给出基于 `pseudoXOF` 的域分离映射描述。
- 大幅改写 `11 Security Claims and Analysis` 的实例化部分：移除 `SHA2/SHA3/SHAKE` 专门论述，改为 ICCS 辅助函数实现口径与现有 generic-analysis 表述。
- 删除 `12 Performance Evaluation` 中 `Additional platforms` 的 TODO 段落。
- 在附录新增 `$q=2^{24}$` 参数说明节（仅三行 `Kylin-128-q24/256-q24/512-q24`），补充动机说明（应用侧对尺寸/验签的诉求 + NIST 4 月 13 日新草案背景）与冻结参数表。
- 完成 `main.tex` 全量编译并通过，新增附录与章节修改均已进入 `main.pdf`。

### 2026-04-25 - Baseline `None` Inference and Bit-Security Verification (Done)

- 对 `paper/code/search_ngcc_params.py` 中四条 baseline 进行了可确定字段推理：`h'`, `log_t/a`, `w/lgw`, `l`, `m`, `sec_level/category`（含映射与公式推导）。
- 依据当前脚本安全公式逐条核验 `bitsec`（按各自 `q`）：
  - `sphincs-a-128s`：`claimed=128.000000`，`verified=126.990060`，差值 `-1.009940`（未达声明值）。
  - `sphincs-a-256s`：`claimed=255.000000`，`verified=255.871964`，差值 `+0.871964`（满足声明值）。
  - `SLH-DSA-SHAKE-128-24`：`verified=127.280773`。
  - `SLH-DSA-SHAKE-256-24`：`verified=255.359352`。
- 导出核验表：`paper/data/para_baselines_inferred_verified.csv`（含推理字段、claimed/verified bitsec、差值与达标标记）。

### 2026-04-25 - Fill Inferred Baseline Numbers Back into Code (Done)

- 按核验结果将可确定推理值回填到 `paper/code/search_ngcc_params.py` 的 `BASELINE_PARAMETERS`：
  - `sphincs-a-128s`：补全 `h'=7`, `m=28`, `category=1`。
  - `sphincs-a-256s`：补全 `h'=6`, `m=47`, `category=5`。
  - `SLH-DSA-SHAKE-128-24`：补全 `log_t=24`, `w=4`, `l=67`, `bitsec=127.28077264423924`, `sec_level=I`。
  - `SLH-DSA-SHAKE-256-24`：补全 `log_t=25`, `w=4`, `l=131`, `bitsec=255.35935186139096`, `sec_level=V`。
- 重新导出 baseline 对照表：`paper/data/para_baselines.csv`。
- 语法与输出检查通过：
  - `python3 -m py_compile paper/code/search_ngcc_params.py`
  - `python3 paper/code/search_ngcc_params.py --print-baselines`

### 2026-04-25 - Six-Profile Search for `q in {2^64,2^24}` and `sec in {128,256,512}` (Done)

- 新增脚本 `paper/code/search_kylin_six_profiles.py`，统一执行六组参数搜索并输出：
  - 六组汇总表 `paper/data/para_kylin_selected_6profiles.csv`
  - 每组全候选明细 `paper/data/param_search_candidates_*.csv`
  - 四张位次图（`{2^64,2^24} x {128,256}`）：`paper/data/param_rank_kylin_{128,256}[ _q24].{png,svg}`
- 规则实现：
  - 命名：`Kylin-{128,256,512}` 与 `Kylin-{128,256,512}-q24`
  - `{128,256}` 采用 bitsec 目标 `{127,255}`，优先尝试“sig/sign/verify 三项均优于 baseline 且最小 sig”
  - `512` 采用规律化搜索（`h` 近 `n`，`a/k/w` 取中等范围）
- 搜索结果：四个 `{q}x{128,256}` 场景在当前口径与范围下均未找到“三项同时严格优于 baseline”的候选（`improve_count=0`），因此输出了“主范围内改进项最多且 sig 最小”的近似最优点，并在汇总表标注 `search_stage=primary-no-strict`、`improves_all_three=False`。
- 兼容性修正：在新脚本中对 `h_vec` 追加 `profile_is_compatible` 过滤，确保输出满足实现约束（避免出现 `h_i > 16`）。

### 2026-04-25 - Constraint Update: `sig`+`verify` Strict, `sign <= 110% baseline` (Done)

- 按新规则更新 `paper/code/search_kylin_six_profiles.py` 的 baseline 约束：
  - `sig < baseline`（严格）
  - `verify_hashcalls < baseline`（严格）
  - `sign_hashcalls <= 110% * baseline`（非严格）
- 汇总表字段同步更新：新增
  - `constraint_sig_lt_baseline`
  - `constraint_verify_lt_baseline`
  - `constraint_sign_le_110pct_baseline`
  - `meets_constraint`
- 重新完成六组搜索与四张图绘制并覆盖产物。
- 结果：
  - `q=2^64` 的 `Kylin-128`、`Kylin-256` 均找到满足新约束的可行解（`meets_constraint=True`，可行数分别 `5/6`）。
  - `q=2^24` 的 `Kylin-128-q24`、`Kylin-256-q24` 在当前口径下仍无可行解（`verify` 严格优于 baseline 未满足）。

### 2026-04-25 - Relax Layer-Height Limit to 32 (Done)

- 将 `paper/code/search_ngcc_params.py` 中 `MAX_LAYER_HEIGHT` 从 `16` 放宽到 `32`。
- `profile_is_compatible` 与后续搜索脚本（调用该检查）将自动采用新上限。
- 快速校验：`h_i=32` 可通过，`h_i=33` 仍拒绝。

### 2026-04-25 - Full Re-run After `MAX_LAYER_HEIGHT=32` (Done)

- 在 `MAX_LAYER_HEIGHT=32` 口径下，按最新约束（`sig` 与 `verify` 严格优于 baseline，`sign <= 110% baseline`）对六组参数全部重跑并覆盖产物。
- 结果更新文件：
  - `paper/data/para_kylin_selected_6profiles.csv`
  - `paper/data/param_search_candidates_*.csv`（6 组）
  - `paper/data/param_rank_kylin_{128,256,128_q24,256_q24}.{png,svg}`
- 结论保持一致：
  - `q=2^64` 的 `Kylin-128`、`Kylin-256` 满足约束（`meets_constraint=True`）。
  - `q=2^24` 的两组仍无满足约束解（`verify < baseline` 未满足）。

### 2026-04-25 - Expanded `a` Range for `q=2^24` (Done)

- 将 `paper/code/search_kylin_six_profiles.py` 中 `q=2^24` 的两组场景参数范围从 `a=8..36` 扩展到 `a=8..64`：
  - `Kylin-128-q24`
  - `Kylin-256-q24`
- 在新范围下完成全量重跑并覆盖输出。
- 结果：`q24` 两组候选规模显著扩大（约 `24.1万` / `34.4万`），但在约束
  - `sig < baseline`
  - `verify < baseline`
  - `sign <= 110% baseline`
  下仍无可行解（`improve_count=0`, `meets_constraint=False`）。

### 2026-04-25 - Canonical Sorted `h_vec` Output (Done)

- 按用户要求，将 `paper/code/search_kylin_six_profiles.py` 中的 `h_vec` 统一改为升序规范形式（直接排好序输出）：
  - baseline 推导后增加 `h_vec = tuple(sorted(h_vec))`。
  - 候选搜索选出最优 profile 后增加 `best_profile = tuple(sorted(best_profile))`。
- 完整重跑六组搜索并覆盖输出文件与四张排名图。
- 校验结果：`para_kylin_selected_6profiles.csv` 中六组 `h_profile` 均为升序，且核心性能指标与约束命中状态保持不变。

### 2026-04-25 - Finalize Six Kylin Profiles (Done)

- 用户确认采用当前六组参数作为最终版本。
- 已固化参数文件：`paper/data/para_kylin_final_6profiles.csv`（由 `para_kylin_selected_6profiles.csv` 复制）。
- 后续文档与实现对齐以该文件为准。
- 定版参数明细（冻结）：
  - `Kylin-128`: `q=2^64, n=16, h=65, d=9, h_vec=[7,7,7,7,7,7,7,8,8], a=13, k=11, w=73, len=22, bitsec=127.209040, sig=6688`
  - `Kylin-256`: `q=2^64, n=32, h=68, d=10, h_vec=[6,6,7,7,7,7,7,7,7,7], a=13, k=22, w=54, len=46, bitsec=255.943778, sig=26784`
  - `Kylin-512`: `q=2^64, n=64, h=70, d=4, h_vec=[17,17,18,18], a=20, k=27, w=64, len=87, bitsec=511.432917, sig=63104`
  - `Kylin-128-q24`: `q=2^24, n=16, h=22, d=1, h_vec=[22], a=24, k=6, w=4, len=67, bitsec=127.280773, sig=3840`
  - `Kylin-256-q24`: `q=2^24, n=32, h=21, d=1, h_vec=[21], a=25, k=12, w=4, len=131, bitsec=255.359352, sig=14880`
  - `Kylin-512-q24`: `q=2^24, n=64, h=57, d=3, h_vec=[19,19,19], a=20, k=24, w=64, len=87, bitsec=511.414568, sig=52672`

### 2026-04-25 - Sync Frozen Parameters Into Code And Docs (Done)

- 已将三组打包实现参数（`q=2^64`）同步到全部 `params.h`：
  - `Implementations/Reference_Implementation/Kylin-{128,256,512}/params.h`
  - `Implementations/Optimized_Implementation/Kylin-{128,256,512}/params.h`
- 为支持非等高 `h_vec`，修复签名/验签层间索引推进逻辑：`kylin_sign.c` 中从第 `i` 层推进到第 `i+1` 层时，改为按 `h_{i+1}` 取位并右移（避免沿用等高假设）。
- 文档与数据已对齐新定版参数：
  - `paper/data/para_ngcc.csv` 改为冻结的 `Kylin-128/256/512` 参数行。
  - `paper/tex/abstract.tex`、`paper/tex/submission_overview.tex`、`paper/tex/submission_checklist.tex`、`paper/tex/kylin.tex`、`paper/tex/kylin-appendix.tex` 已移除旧的统一 `(70,10,14,64)` 叙述并更新为定版口径。
  - `Implementations/README` 补充当前冻结实现参数。
- `paper/code/search_ngcc_params.py` 默认行为已更新：在 `q=2^64` 且未显式给 `--shape` 时，直接输出冻结打包参数，避免 `make` 流程将 `para_ngcc.csv` 回滚到旧值。
- 快速验证：
  - `python3 paper/code/search_ngcc_params.py --write-csv paper/data/para_ngcc.csv` 通过并生成新表。
  - `python3 -m py_compile paper/code/search_ngcc_params.py` 通过。
  - `python3 paper/code/para.sage` 通过（输出与冻结参数一致）。
  - `Kylin-128/256`（ref+opt）`make && make test` 通过；`Kylin-512`（ref+opt）`make` 编译通过（`make test` 运行较慢，已做编译级验证）。

### 2026-04-25 - Remove >50MB Non-Essential Artifacts for GitHub Push (Done)

- 扫描工作区（排除 `.git/`）后，定位到 4 个超过 50MB 的非必要大文件（参数搜索中间产物/排名图）：
  - `paper/data/param_rank_kylin_128.svg`（64MB）
  - `paper/data/param_rank_kylin_256.svg`（102MB）
  - `paper/data/param_search_candidates_kylin_128_q24.csv`（1.2GB）
  - `paper/data/param_rank_kylin_128_q24.svg`（3.2GB）
- 校验主文档与代码依赖：上述文件未被 `main.tex` 直接引用，`param_search_candidates_kylin_128_q24.csv` 仅作为冻结参数表中的路径说明字段。
- 已删除上述 4 个大文件，删除后复扫确认：工作区（排除 `.git/`）已无 `>50MB` 文件。
- 更新 `.gitignore`，避免同类产物再次误提交：
  - `paper/data/param_rank_*.svg`
  - `paper/data/param_search_candidates_*_q24.csv`

### 2026-04-25 - Add Missing `Kylin-{128,256,512}-q24` Implementations (Done)

- 补齐缺失的 `q=2^24` 三组实现目录（参考实现 + 优化实现）：
  - `Implementations/Reference_Implementation/Kylin-128-q24`
  - `Implementations/Reference_Implementation/Kylin-256-q24`
  - `Implementations/Reference_Implementation/Kylin-512-q24`
  - `Implementations/Optimized_Implementation/Kylin-128-q24`
  - `Implementations/Optimized_Implementation/Kylin-256-q24`
  - `Implementations/Optimized_Implementation/Kylin-512-q24`
- 每组新目录已同步 NGCC 实例标识与构建实例名：
  - `SIG_AlgorithmInstance.h` 中 `ALGORITHM_INSTANCE` 改为 `Kylin-*-q24`
  - `Makefile` 中 `INSTANCE` 改为 `Kylin-*-q24`
- 按冻结参数文件 `paper/data/para_kylin_final_6profiles.csv` 回填 6 组 `params.h`：
  - `Kylin-128-q24`: `n=16, h=22, d=1, h_vec=[22], a=24, k=6, w=4, len=67`
  - `Kylin-256-q24`: `n=32, h=21, d=1, h_vec=[21], a=25, k=12, w=4, len=131`
  - `Kylin-512-q24`: `n=64, h=57, d=3, h_vec=[19,19,19], a=20, k=24, w=64, len=87`
- 修复 `q24` 低层高配置的编译告警：在 6 个新目录 `hash_iccs.c` 中把 `SPX_TREE_BITS/SPX_LEAF_BITS` 掩码逻辑改为编译期分支（避免 `SPX_TREE_BITS==0` 时出现移位宽度告警）。
- 更新实现包说明文档 `Implementations/README`：实例列表与冻结参数补全为六组。
- 更新 `Implementations/tools/collect_metrics.py`：实例目录改为自动发现 `Kylin-*`，避免硬编码仅三组导致漏统计。
- 验证：
  - 6 个新增目录均 `make clean && make` 编译通过（ref + opt）。
  - `python3 -m py_compile Implementations/tools/collect_metrics.py` 通过。
  - `Reference/Kylin-128-q24` 功能自测在 180 秒超时窗口内未完成（`timeout` 退出码 `124`）；符合 q24 变体较慢预期，需在更长时间窗口做完整运行验证。

### 2026-04-26 - Kylin-128 Optimized Path Deepening (Done)

- 仅针对 `Implementations/Optimized_Implementation/Kylin-128` 做深度优化，未改参数集与接口行为。
- 主要优化项：
  - `auxfunc.c`：
    - 重构 SM3 压缩核心为无轮内分支版本（`i<16` 与 `i>=16` 分离），并引入旋转常量表。
    - 增加 x86 运行时分发：`AVX2+BMI2` 可用时启用 SIMD 加载路径，其他平台自动回落标量路径。
    - `pseudoXOF` 新增字节对齐快路径，改为直接计算 `SM3(msg || ct)`，移除热路径堆分配和大块临时拷贝。
  - `hash_iccs.c`、`thash_iccs.c`：
    - 高频组包从 `malloc/free` 改为栈缓冲优先（超限再回退堆分配），降低签名路径分配开销。
  - `Makefile`（优化实现 `Kylin-128`）：
    - 默认优化编译参数升级为 `-O3 -march=native -flto -fomit-frame-pointer -funroll-loops -fno-plt`，链接增加 `-flto -fno-plt`。
  - `Implementations/README`：
    - 更新说明为 `Kylin-128` 已包含代码级优化（不再是仅编译参数区分）。
- 正确性回归：
  - `Reference_Implementation/Kylin-128` 与 `Optimized_Implementation/Kylin-128` 的 `KAT_SIG` 输出 `sha256` 一致：
    - `41143927762b70429d98e3aeb50c5835afd7a0e7ef2ad6a48420720f4e98a4c3`
  - `make test`（opt）通过。
- 性能结果（默认口径，9 轮中位数，单位 ms）：
  - `Reference`：`keygen=311.633`, `sign=1868.617`, `verify=5.303`
  - `Optimized`：`keygen=280.359`, `sign=1701.369`, `verify=4.979`
  - 倍数 `ref/opt`：`keygen=1.112x`, `sign=1.098x`, `verify=1.065x`

### 2026-04-26 - Move `q=2^24` Profiles to `Additional_Implementation` (Done)

- 按决策将三组 `q=2^24` 实现从主实现目录迁移到 Additional 目录，并保留完整代码历史（`git mv`）：
  - `Implementations/Reference_Implementation/Kylin-*-q24 -> Implementations/Additional_Implementation/Reference_Implementation/Kylin-*-q24`
  - `Implementations/Optimized_Implementation/Kylin-*-q24 -> Implementations/Additional_Implementation/Optimized_Implementation/Kylin-*-q24`
- 同步更新工程自动化，保证迁移后构建、KAT 与指标收集不漏项：
  - 顶层 `Makefile` 已纳入 Additional 目录实例扫描，`kat` 目标同时覆盖主参考与 Additional 参考目录。
  - `Implementations/tools/collect_metrics.py` 已扩展为同时发现主实现与 Additional 实现实例。
- 同步更新记录文档：
  - `AGENTS.md`（主提交三组 + Additional 三组的定位）
  - `Implementations/README`（目录结构与命令示例）
  - `docs/README.md`（仓库实现布局更新说明）
  - `paper/tex/submission_overview.tex`、`paper/tex/submission_checklist.tex`（将 q24 三组标注为 Additional 实现）

### 2026-04-26 - Flatten `Additional_Implementation` to Ref-Only Layout (Done)

- 按最新决定，`Additional_Implementation` 不再区分 `Reference_Implementation` 与 `Optimized_Implementation` 子目录，只保留 Ref 版本：
  - `Implementations/Additional_Implementation/Kylin-128-q24`
  - `Implementations/Additional_Implementation/Kylin-256-q24`
  - `Implementations/Additional_Implementation/Kylin-512-q24`
- 目录迁移与清理：
  - 已将 `Additional_Implementation/Reference_Implementation/Kylin-*-q24` 拉平迁移至 `Additional_Implementation/Kylin-*-q24`。
  - 已删除 `Additional_Implementation/Optimized_Implementation/` 下三组 `q24` 目录。
- 工程脚本同步：
  - 顶层 `Makefile` 改为扫描 `Implementations/Additional_Implementation/Kylin-*`。
  - `Implementations/tools/collect_metrics.py` 改为直接发现 `Implementations/Additional_Implementation/Kylin-*`，并将 Additional 实例标记为 `ref`。
- 文档同步：
  - `AGENTS.md`、`Implementations/README`、`docs/README.md`、`paper/tex/submission_overview.tex`、`paper/tex/submission_checklist.tex` 已更新为 “Additional 仅 Ref” 口径。

### 2026-04-26 - Draft Cleanup: Remove Empty Inputs and `q=2^80` Wording (Done)

- 按“今天出初稿”的收敛目标完成文稿结构与口径清理：
  - `main.tex` 移除空章节输入：`paper/tex/preliminary`、`paper/tex/revisit`、`paper/tex/results`（三个文件保留但不再纳入主文稿）。
  - `paper/tex/submission_overview.tex` 删除 `2^80` 相关 TODO，改为明确单钥 `q=2^64` 的一致口径。
  - `paper/tex/submission_checklist.tex` 删除 `2^80` 相关 TODO，改为“安全表已按 `q=2^64` 对齐”的完成态描述。
  - `paper/tex/kylin.tex` 的 repeated-key 条目删除 `q <= 2^80` 扩展解释，仅保留 `q=2^64` 目标声明。
- 验证：
  - 关键词复扫：`paper/tex` 与 `main.tex` 中已无 `2^80` / `q<=2^80` 表述。
  - 编译验证：`latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error -outdir=/tmp/kylin-draftcheck main.tex` 通过，输出 `/tmp/kylin-draftcheck/main.pdf`。

### 2026-04-26 - Draft Cleanup: Replace Remaining `spa_*` Markers with `kylin_*` (Done)

- 清理文稿中残留的旧算法入口记号：
  - `paper/tex/kylin.tex` 中三处 `\inputminted` 已从 `paper/code/spa_*.cs` 改为 `paper/code/kylin_*.cs`。
  - 文中展示的 keygen/sign/verify 伪代码入口统一为 `kylin_keygen`、`kylin_sign`、`kylin_verify`。
- 同步整理代码示例文件名：
  - `paper/code/spa_keygen.cs -> paper/code/kylin_keygen.cs`
  - `paper/code/spa_sign.cs -> paper/code/kylin_sign.cs`
  - `paper/code/spa_verify.cs -> paper/code/kylin_verify.cs`
- 验证：
  - 关键词复扫：`paper/tex` 与 `paper/code` 中已无 `spa_` 残留。
  - 编译验证：`latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error -outdir=/tmp/kylin-spa-clean main.tex` 通过，输出 `/tmp/kylin-spa-clean/main.pdf`。

### 2026-04-26 - Draft Polish: Fix `\len`, Remove File-Path Mentions, Reorder Section 3.1 (Done)

- 修复 `\len` 宏的正文渲染与间距：
  - `paper/tex/defs.tex` 中为 `\len` 补上 `\xspace`，使其在正文中按 `len` 稳定显示并保留自然空格。
- 调整第 3 节结构与引导语：
  - `paper/tex/construction.tex` 在 `3 Kylin vs. SPHINCS+` 开头补充一句，明确除了 `\WOTSCS` 编码优化外，还采用了更灵活的 hypertree 分层。
  - 将 `Diverse Layer Heights in the Hypertree` 提前为 `3.1`，原 `The WOTS+ Encoding` 顺延为 `3.2`。
- 收紧论文中的仓库材料引用口径：
  - `paper/tex/abstract.tex`、`paper/tex/submission_overview.tex`、`paper/tex/submission_checklist.tex`、`paper/tex/kylin-appendix.tex` 中移除正文里直接显示的 `.csv`、`.py`、`.txt`、`.zip` 路径/文件名，改为自然语言描述。
  - 保留 LaTeX 内部 `\csvreader` / `\inputminted` 输入路径，不影响排版生成。
- 验证：
  - 编译验证：`latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error -outdir=/tmp/kylin-doc-polish main.tex` 通过，输出 `/tmp/kylin-doc-polish/main.pdf`。
  - 成品核对：PDF 文本中已出现 `3.1 Diverse Layer Heights in the Hypertree` 与 `3.2 The WOTS+ Encoding`。

### 2026-04-26 - Draft Polish: Rename `\len` Macro to Avoid CSV Collision (Done)

- 定位到 `\len` 长期渲染异常的根因：
  - `paper/tex/submission_overview.tex` 使用 `\csvreader[head to column names]` 读取参数表；
  - CSV 表头中存在 `len` 列，导致 `\len` 被 `csvsimple` 当作列宏占用，后续正文中的 `\len` 发生冲突。
- 修复方式：
  - 将论文正文里的长度宏从 `\len` 统一重命名为 `\wotslen`；
  - `paper/tex/defs.tex` 改为 `\newcommand{\wotslen}{\ensuremath{\mathtt{len}}\xspace}`；
  - `paper/tex/kylin.tex` 中所有正文/公式/复杂度表达里的 `\len` 均同步替换为 `\wotslen`；
  - 保留 `submission_overview.tex` 表格行模板中的 `\len`，该处继续作为 CSV 列值宏使用。
- 验证：
  - 编译验证：`latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error main.tex` 通过，并刷新仓库根目录 `main.pdf`。
  - 成品抽查：PDF 文本中原先异常位置现已正确显示为 `len`，例如 “`CS-WOTS+ uses the parameters n, w and len`” 与 “`the values m and len are computed`”。

### 2026-04-26 - Reorganize Paper Chapters Around NGCC Submission Requirements (Done)

- 按 `docs/Submission Requirements for Public-Key Cryptographic Algorithms.md` 的提交包结构重排主文档章节：
  - 将文稿前部改为 `Submission Package Overview` 与 `Basic Information` 两节；
  - 明确说明 Sections `3--14` 共同构成算法规格部分；
  - 在正文新增 `Implementation Codes`、`Test Vectors`、`Intellectual Property Statements` 三节，使主文档顺序与 NGCC 要求一致。
- 具体文稿调整：
  - `paper/tex/submission_overview.tex` 重写为提交包映射总览 + 基本信息结构，并保留冻结的三组主参数表；
  - `paper/tex/intro.tex`、`paper/tex/construction.tex`、`paper/tex/kylin.tex` 的章节标题按“算法描述/设计差异/安全/性能/特性声明”口径重命名；
  - `paper/tex/kylin.tex` 将 correctness/failure-probability 说明并入 `Security Statements and Analyses`；
  - 新增 `paper/tex/implementation_codes.tex`、`paper/tex/test_vectors.tex`、`paper/tex/intellectual_property.tex` 三个正文文件；
  - `main.tex` 更新主文档引入顺序；
  - `paper/tex/submission_checklist.tex` 改名为面向外部交付的附录清单，并同步更新相关交叉引用。
- 验证：
  - 编译验证：`latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error main.tex` 通过，并刷新仓库根目录 `main.pdf`。
  - 目录抽查：成品 TOC 现已按 `Overview -> Basic Information -> Algorithm Description/Design/Security/Performance/Features -> Implementation Codes -> Test Vectors -> Intellectual Property Statements -> Appendices` 的顺序展开。

### 2026-04-26 - Rename Remaining Legacy `sphincsp*.tex` Filenames to `kylin*` (Done)

- 清理论文源码中的遗留文件命名：
  - 论文主体 `.tex` 文件已统一改为 `kylin` 命名。
  - 论文附录 `.tex` 文件已统一改为 `kylin-appendix` 命名。
  - 相关 benchmark figure 的 `.tex` 文件也已同步改为 `kylin` 命名。
- 同步更新入口与记录：
  - `main.tex` 的 `\input{...}` 已改为新的 `kylin` / `kylin-appendix` 路径。
  - `plan.md` 中此前记录到的旧路径已一并改成新的 Kylin 命名，避免仓库继续保留旧的论文文件命名。
- 验证：
  - 关键词复扫：仓库受管文件中已不再出现旧的 `sphincsp*.tex` 论文文件路径。
  - 编译验证：`latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error main.tex` 通过，并刷新仓库根目录 `main.pdf`。

### 2026-04-26 - Spec Scope Cleanup + Chapter Split + Citation Updates (Done)

- 规范范围收敛（specification only）：
  - 从 `main.tex` 移除不属于 specification 正文的章节输入：`Implementation Codes`、`Test Vectors`、`Intellectual Property Statements` 与 `Packaging Checklist`。
- 章节结构重组：
  - 将第 9--12 章拆分为独立文件并接入主文档：
    - `paper/tex/design_rationale.tex`
    - `paper/tex/security_statements_and_analyses.tex`
    - `paper/tex/performance_evaluation.tex`
    - `paper/tex/feature_statements.tex`
  - `paper/tex/kylin.tex` 截断为前置章节；`main.tex` 改为分文件输入上述四章。
- 文本与内容清理：
  - 删除安全章节中的两条 TODO（formal model / additional security-property analyses）。
  - 删除安全章节中 `Concrete generic-security figures` 表（Table 4）。
  - 在 `2.1 Diverse Layer Heights in the Hypertree` 增加默认有序约束：`h_0 <= h_1 <= ... <= h_{d-1}`。
  - 将 Table 1 表头 `KeyGen/Sign/Verify (Hashcall)` 改为不带括号后缀。
- 相关工作与附录引用补充：
  - 在 `Stateless signatures` 段落加入并整合引用：`SP:HKRY23`、`C:KhoKudWag25`、`EPRINT:QinSun25`、`optimalwots`，并加入 NIST FIPS 205 引用。
  - 在 Appendix B (`q=2^24 Companion Parameter Profiles`) 加入 NIST 2026-04-13（SP 800-230 IPD）引用说明。
  - `paper/bib/extra.bib` 新增 `NIST:FIPS205` 与 `NIST:SP800-230-IPD` 条目。
- 验证：
  - 使用 `latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error main.tex` 编译通过，`main.pdf` 更新。

### 2026-04-30 - Build NGCC Electronic Submission Package (Done)

- 重新构建英文算法文本：`make -C paper/build all` 通过，并将当前 `main.pdf` 复制为 `build/算法文本.pdf`。
- 重新生成 fresh `build/` 提交暂存树：
  - 根目录包含 `算法基本信息.pdf`、`算法文本.pdf`、`知识产权声明.pdf`、`Implementations/`、`Test_Vectors/`；
  - 主提交三档 `Kylin-128`、`Kylin-256`、`Kylin-512` 保留在 `Reference_Implementation/` 与 `Optimized_Implementation/`；
  - q24 伴随实现从源码树的 `Additional_Implementation/Optimized_Implementation/Kylin-*-q24` 提升为包内扁平 `Additional_Implementation/Kylin-*-q24`。
- 重写 `build/Implementations/README`，只描述最终包内实际 shipped 目录、q24 扁平布局和实例目录内容。
- 打包生成 `build/Kylin-0430.zip`，SHA-256 为 `339d90dc91118e900df2ab5fd3c30ea65d2d191b2dbfbb18ee556295a859e7e7`。
- 验证：
  - `make clean build test` 通过主提交 Ref/Opt 六个实例，包括 `Kylin-512`；
  - q24 优化实现三档 `make clean all` 通过，并修复其 `hash_iccs.c` 中 `SPX_TREE_BITS/SPX_LEAF_BITS` 常量移位告警；
  - zip 清单检查确认无旧 zip、无嵌套 Additional 实现层级、无 `tools/`、`benchmarks/`、`output/`、`.stack-usage/` 或生成的可执行文件；
  - 从 zip 解包后，主提交 Ref/Opt 六个实例 `make clean all test` 通过；按要求未将 q24 `make test` 作为默认验证项。

### 2026-06-23 - Migrate Kylin Few-Time Layer from FORS to BPORS+FP (Done)

- 将 Kylin 的 few-time signature 层从 FORS 替换为 BPORS+FP：
  - 在主提交与 q24 伴随提交的 Reference/Optimized 共 12 个实例中新增 `bpors.c`/`bpors.h`，删除 `fors.c`/`fors.h`；
  - `kylin_sign.c`、`hash_iccs.c`、`SIG_AlgorithmInstance.c`、`params.h`、`Makefile` 与地址类型常量同步改为 BPORS+FP；
  - 保持外层 Kylin 参数 `n,h,d,h_vec,w,len` 不变，并为六个冻结 profiles 固定 BPORS+FP 参数与签名长度。
- 同步英文与中文文档：
  - `paper/tex/kylin.tex` 与 `paper/tex-zh/kylin.tex` 新增 BPORS+FP 规格、签名格式、算法伪代码与参数表；
  - `paper/tex/security_statements_and_analyses.tex` 与中文镜像补入 BPORS+FP game proof、single-instance cover-security、multi-instance theorem、Kylin reduction theorem 和 HK22/SPHINCS+ comparison；
  - 参数 CSV、术语表、EN->ZH 同步指南、实现 README 与伪代码文件同步更新。
- 固定参数检查：
  - `Kylin-128`: `K=5,B=6,t=132,k=4,mmax=120`, signature `6472` bytes, concrete bit security `127.999038489`；
  - `Kylin-256`: `K=7,B=7,t=280,k=5,mmax=235`, signature `25576` bytes, concrete bit security `255.999998892`；
  - `Kylin-512`: `K=13,B=7,t=512,k=5,mmax=490`, signature `95432` bytes, concrete bit security `511.999999933`；
  - q24 companion profiles remain size-first and meet their target levels under the BPORS+FP checker.
- 验证：
  - `python3 paper/code/check_bpors_profiles.py` 通过；
  - 主提交 Reference/Optimized 六个实例 `make clean && make test` 全部通过，包括 `Kylin-512`；
  - q24 Reference/Optimized 六个实例 `make clean && make` 全部通过，且 `Optimized_Implementation/Kylin-128-q24 make test` 通过；其余 q24 测试因 size-first 参数耗时较长，未纳入默认收口验证；
  - `make -C paper/build all` 与 `make -C paper/build zh` 均通过；
  - `git diff --check` 通过，活跃实现代码中未检出 `FORS/SPX_FORS/fors` 残留。

### 2026-06-24 - Build BPORS-Retuned NGCC Electronic Submission Package (Done)

- 按 `docs/公钥密码算法提交要求.md` 重新构建电子版提交材料：
  - `make -C paper/build all` 通过，并将最新英文 `main.pdf` 复制为 `build/算法文本.pdf`；
  - fresh `build/` 根目录包含 `算法基本信息.pdf`、`算法文本.pdf`、`知识产权声明.pdf`、`Implementations/`、`Test_Vectors/`；
  - 主提交 `Kylin-128/256/512` 保留在 `Reference_Implementation/` 与 `Optimized_Implementation/`；
  - q24 伴随实现从源码树 `Additional_Implementation/Optimized_Implementation/Kylin-*-q24` 提升为包内扁平 `Additional_Implementation/Kylin-*-q24`。
- 重写包内 `build/Implementations/README`，只描述最终 shipped 树与实例源文件；同时清理包内 Makefile，使其不再引用仓库本地 `tools/`、benchmark 或 stack-usage 目标，最终包内实例可独立 `make`、`make test`、`make kat`。
- 生成最终压缩包 `build/Kylin-0624.zip`，大小约 7.8 MB，SHA-256 为 `06ccdc7804472c0ced999f65f9c9f544df493b603698fed1dce8a24d35699fa2`。
- 验证：
  - 主提交 Ref/Opt 六个包内实例 `make clean all test` 通过，包括 `Kylin-512`；
  - q24 Additional 三个包内实例 `make clean all` 通过；q24 `make test` 未作为默认打包烟测；
  - 六个 KAT 文件均在 `build/Test_Vectors/` 中，每个 120 行，SHA-256 与仓库根 `Test_Vectors/` 一致；
  - `zipinfo` 检查确认压缩包不含自身、`tools/`、`benchmarks/`、`output/`、`.stack-usage/`、对象文件、栈报告或生成的可执行文件，且 Additional q24 没有嵌套 `Reference_Implementation/` 或 `Optimized_Implementation/` 层级。

### 2026-06-24 - Refresh Table 1 and Rebuild Electronic Package (Done)

- 更新英文 `paper/figure/sha256-simple-comp.tex` 及中文镜像 `paper/figure-zh/sha256-simple-comp.tex` 中的 Table 1，使三组主实例的 KeyGen/Sign/Verify hashcall 与签名大小对齐最终 BPORS retuned 参数：
  - `Kylin-128`: `417279 / 2389373 / 7362`, signature `6472` bytes；
  - `Kylin-256`: `324095 / 3382025 / 11405`, signature `25352` bytes；
  - `Kylin-512`: `519295 / 6493104 / 44418`, signature `91528` bytes。
- 重新构建英文与中文论文：`make -C paper/build all && make -C paper/build zh` 通过；`pdftotext -layout` 抽查确认 `main.pdf` 和 `build/算法文本.pdf` 中的 Table 1 已显示新值。
- 重新生成电子提交包 `build/Kylin-0624.zip`，SHA-256 为 `8fef9179b5355723e33ce0f35dceeca771c366bc1752ee8e046b7fa103c8fa73`。
- 验证：主提交 Ref/Opt 六个包内实例 `make clean all test` 通过；q24 Additional 三个包内实例 `make clean all` 通过；zip 清单仍为 321 项且不含 `tools/`、`benchmarks/`、`output/`、`.stack-usage/`、对象文件、栈报告、生成的可执行文件或嵌套 Additional 实现层级。

### 2026-06-25 - q64 Exact and q24 Legacy BPORS+FP Parameter Search (Done)

- 重新搜索并冻结混合目标标签的 BPORS+FP 参数：主提交 q64 版本保持精确 `128.0/256.0/512.0`，q24 companion 版本按本次要求使用 legacy `127.0/255.0/511.0`。主提交 q64 版本继续对标 ePrint 2022/059 的 SPHINCS-alpha SHA2 small-signature 指标，q24 128/256 版本对标 SP 800-230 limited-signature-use 指标；512 档约束为不超过所选 256 档的 4 倍。
- 当前冻结参数为：
  - `Kylin-128`: `h=56,d=4,h_vec=[14,14,14,14], BPORS=(3,15,896,7,136), w=114, len=20, sig=4712`;
  - `Kylin-256`: `h=58,d=4,h_vec=[15,15,15,13], BPORS=(5,13,1024,7,241), w=127, len=38, sig=15592`;
  - `Kylin-512`: `h=62,d=4,h_vec=[16,16,16,14], BPORS=(12,14,192,6,419), w=125, len=75, sig=54664`;
  - `Kylin-128-q24`: `h=18,d=1,h_vec=[18], BPORS=(2,15,2048,6,85), w=7, len=48, sig=2632`, `bitsec=127.444703`;
  - `Kylin-256-q24`: `h=18,d=1,h_vec=[18], BPORS=(5,16,224,8,197), w=5, len=113, sig=11816`, `bitsec=255.999944`;
  - `Kylin-512-q24`: `h=32,d=2,h_vec=[16,16], BPORS=(7,12,768,8,344), w=12, len=145, sig=46280`, `bitsec=511.504374`.
- 重要约束说明：在包含 `2^{-8n}` 直接猜测项的 checker 模型下，q64 profile 的指数从下方逼近 `128/256/512`；checker 采用 `1e-12` 高精度数值容差验证精确 target 标签。q24 profile 改用 legacy `127/255/511` 目标后，`Kylin-128-q24` 签名尺寸从 exact-q24 的 `3928` 字节降至 `2632` 字节，同时仍满足 SP 800-230 的 keygen/sign/verify/signature cap。`Kylin-512-q24` 需要反推更大的 `Kylin-256-q24` 支撑 profile，因此 `Kylin-256-q24` 最终采用 `11816` 字节而不是初选的 `10888` 字节。
- 已完成：`paper/data/para_kylin_final_6profiles.csv`、`para_kylin_selected_6profiles.csv`、12 个实现目录的 `params.h`、英文/中文参数表、安全表、性能 hashcall 表、实现 README、`AGENTS.md` 与 impact note 同步更新。
- 验证：`python3 -m py_compile paper/code/search_sphincs_compare_params.py paper/code/search_bpors_kylin_params.py paper/code/check_bpors_profiles.py` 通过；`python3 paper/code/check_bpors_profiles.py` 通过；12 个 Reference/Optimized/Additional 实现目录 `make clean all` 通过；`make -C paper/build all` 与 `make -C paper/build zh` 均通过；`git diff --check` 通过。q24 KAT 生成、wall-clock benchmark 刷新和提交包重打包仍待单独长任务收口。

### 2026-06-25 - Correct SPHINCS-alpha Hashcall Cap Interpretation (Blocked)

- 复查 SPHINCS-alpha 2022/059 / NIST 提交版后确认：`537,033,762` 与 `764,352,612` 来自 SPHINCS-alpha SHA2 AVX2 benchmark 表，单位是 CPU cycles，不是 parameter-search hashcall。
- 修正 `paper/code/search_sphincs_compare_params.py`：q64 SPHINCS-alpha cap 改为按 Section 8.1.1 / Appendix A 的理论 hashcall proxy 从参数公式计算，避免再次把 cycle 表误用为 hashcall cap。
- 修正后的 SPHINCS-alpha theoretical proxy caps 为：
  - `SPHINCS-alpha-128s`: signature `6880`, keygen `208639`, sign `2047872`, verify `7369`;
  - `SPHINCS-alpha-256s`: signature `27232`, keygen `215167`, sign `2713408`, verify `18418`.
- 重新搜索严格目标 `q64 exact 128/256/512`, `q24 legacy 127/255/511`, `Kylin-512 <= 4x Kylin-256` 时，`Kylin-128` 已无可行解：在 `sig<=6880`, `keygen<=208639`, `sign<=2047872`, `verify<=7369`, `bitsec>=128` 下 full BPORS 宽搜索失败。
- 约束剥离诊断：
  - 放开 keygen cap 仍无解；
  - 保持 `sig<=6880` 时，满足精确 128 安全的最小 sign proxy 仍约为 `7.69e29`，问题来自 BPORS+FP forced-pruning 的 `1/tau` 项；
  - 放开 signature cap、保留 keygen/sign/verify cap 与精确 128 安全时，最小签名为 `8616` bytes；
  - 同样放开 signature cap 的精确 256 诊断点为 `28840` bytes。
- 结论：严格“所有 q64 指标均不超过 SPHINCS-alpha small-signature theoretical hashcall proxy 且安全精确达标”与当前 BPORS+FP 构造冲突；因此本次未静默改写 `paper/data/para_kylin_final_6profiles.csv` 或实现参数，等待明确选择放宽 signature cap、sign cap 或改回其他对标口径。

### 2026-06-25 - Legacy 127/255/511 BPORS+FP Retune under Corrected Caps (Done)

- 按最新要求放弃 q64 精确 `128/256/512` target，改回 legacy `127/255/511` 安全阈值；q64 128/256 继续使用 SPHINCS-alpha theoretical keygen/sign/verify hashcall caps，修正后的 signature-size cap 不再作为硬约束，而是在这些时间 cap 下最小化 Kylin 签名尺寸。
- 搜索脚本新增 `--relax-q64-signature-caps` 与 `--q64-signature-slack`，用于显式记录“放松 q64 signature cap、保留 hashcall cap”的再现路径。
- 当前冻结参数更新为：
  - `Kylin-128`: `h=56,d=8,h_vec=[7,7,7,7,7,7,7,7], BPORS=(6,8,192,5,158), w=43, len=25, sig=7128`, `bitsec=127.568928`, `sign/verify=2038881/4482`;
  - `Kylin-256`: `h=58,d=10,h_vec=[5,6,6,6,6,6,6,6,5,6], BPORS=(9,7,256,6,281), w=71, len=43, sig=26376`, `bitsec=255.607621`, `sign/verify=2691224/15507`;
  - `Kylin-512`: `h=62,d=9,h_vec=[7,7,7,7,7,7,7,7,6], BPORS=(15,7,320,5,457), w=103, len=78, sig=83016`, `bitsec=511.422193`, `sign/verify=10723949/36480`;
  - q24 rows remain `Kylin-128-q24 sig=2632`, `Kylin-256-q24 sig=11816`, `Kylin-512-q24 sig=46280` under the prior legacy/support-profile logic.
- 已同步：`paper/data/para_kylin_final_6profiles.csv`、`para_kylin_selected_6profiles.csv`、primary Ref/Opt `params.h`、`AGENTS.md`、`Implementations/README`、hashcall/package-bench CSV、英文/中文 Table 1、参数表、安全表、性能表与 impact note。
- 验证：`python3 -m py_compile paper/code/search_sphincs_compare_params.py paper/code/search_bpors_kylin_params.py paper/code/check_bpors_profiles.py` 通过；`python3 paper/code/check_bpors_profiles.py` 通过；主提交 Reference/Optimized 三档 `make clean all test` 均通过，包括 `Kylin-512`；`make -C paper/build all` 与 `make -C paper/build zh` 均通过；`git diff --check` 通过。KAT/Test Vectors 与 package rebuild 仍需后续长任务刷新。

### 2026-06-25 - SLH-DSA/SP 800-230 Legacy 127/255/511 Retune (Done)

- 按最新要求将安全阈值切回 legacy `127/255/511`，并重新搜索六组 BPORS+FP 参数。约束口径为：q64 `Kylin-128/256` 对标 SLH-DSA SHAKE sign/verify hashcall cap，q24 `Kylin-128-q24/256-q24` 对标 SP 800-230 limited-signature-use sign/verify cap；keygen 不作为硬约束；q64 `Kylin-512` 不超过所选 `Kylin-256` 的 4 倍 sign/verify cap；`Kylin-512-q24` 直接对标外部 SP 800-230 `Kylin-256-q24` profile 的 4 倍 sign/verify cap，未反推放大 `Kylin-256-q24`。
- 本轮还修正了 HT frontier pruning：支配关系现在要求 retained HT profile 的总高度 `h` 不小于被剪枝 profile，避免低高度 profile 错误剪掉高高度可行候选。
- 当前冻结参数更新为：
  - `Kylin-128`: `h=62,d=7,h_vec=[8,9,9,9,9,9,9], BPORS=(4,7,128,6,95), w=17, len=33, sig=6616`, `bitsec=127.054520`, `sign/verify=2113168/2060`;
  - `Kylin-256`: `h=65,d=8,h_vec=[8,8,8,8,8,8,8,9], BPORS=(9,8,66,5,187), w=16, len=66, sig=26440`, `bitsec=255.155647`, `sign/verify=2912473/4310`;
  - `Kylin-512`: `h=64,d=8,h_vec=[8,8,8,8,8,8,8,8], BPORS=(14,8,256,5,415), w=43, len=96, sig=84360`, `bitsec=511.663268`, `sign/verify=11566744/16755`;
  - `Kylin-128-q24`: `h=21,d=1,h_vec=[21], BPORS=(2,16,560,7,76), w=7, len=48, sig=2568`, `bitsec=127.163327`, `sign/verify=1289759302/270`;
  - `Kylin-256-q24`: `h=20,d=1,h_vec=[20], BPORS=(3,15,2944,8,184), w=7, len=94, sig=10344`, `bitsec=255.321235`, `sign/verify=1783882624/535`;
  - `Kylin-512-q24`: `h=38,d=2,h_vec=[19,19], BPORS=(7,16,216,10,313), w=12, len=145, sig=45576`, `bitsec=511.529371`, `sign/verify=7342274265/2089`.
- 已同步：`paper/data/para_kylin_final_6profiles.csv`、`para_kylin_selected_6profiles.csv`、12 个实现目录 `params.h`、`AGENTS.md`、`Implementations/README`、hashcall/package-bench CSV、英文/中文参数表、安全表、q24 附录、性能表、Table 1 figure 源与 impact note。
- 验证：`python3 -m py_compile paper/code/search_sphincs_compare_params.py paper/code/search_bpors_kylin_params.py paper/code/check_bpors_profiles.py` 通过；`python3 paper/code/check_bpors_profiles.py` 通过；主提交 Reference/Optimized 三档 `make clean all test` 均通过，包括 `Kylin-512`；q24 Reference/Optimized 六个目录 `make clean all` 通过；`make -C paper/build all` 与 `make -C paper/build zh` 均通过；`git diff --check` 通过。q24 `make test`、KAT/Test Vectors、wall-clock benchmark 与 package rebuild 仍需后续长任务刷新。

### 2026-06-26 - BPORS Sampler Cost Fix, q24 Tau-Floor Retune, and Full KAT Refresh (Done)

- 精简 BPORS+FP counter 尝试路径：12 个实现目录的 `bpors.c` 同步改为 512-byte sampler block，bucket 与 index 使用独立 domain；失败 counter 只解析 index 子集并计算 Octopus 认证节点数，成功后才抽 bucket 并生成秘密值、子树与外层认证路径。
- 修正搜索/checker hashcall 模型：sign proxy 现在显式计入 sampler block 与 `1/\tau` 的 index-sampling 重试成本，verify proxy 使用一次 index sampler 与一次 bucket sampler；`search_sphincs_compare_params.py` 增加 `--tau-floor` / `--q24-tau-floor`，本轮 q24 使用 `--q24-tau-floor 1e-4`。
- 当前冻结参数更新为：
  - `Kylin-128`: `h=62,d=7,h_vec=[8,9,9,9,9,9,9], BPORS=(4,7,128,6,95), w=17, len=33, sig=6616`, `bitsec=127.054520`, `sign/verify=2113169/2062`;
  - `Kylin-256`: `h=65,d=8,h_vec=[8,8,8,8,8,8,8,9], BPORS=(9,8,66,5,187), w=16, len=66, sig=26440`, `bitsec=255.155647`, `sign/verify=2912474/4312`;
  - `Kylin-512`: `h=64,d=8,h_vec=[8,8,8,8,8,8,8,8], BPORS=(14,8,256,5,415), w=43, len=96, sig=84360`, `bitsec=511.663268`, `sign/verify=11566745/16757`;
  - `Kylin-128-q24`: `h=22,d=1,h_vec=[22], BPORS=(2,12,864,7,90), w=6, len=52, sig=2872`, `bitsec=127.150459`, `tau=1.00366813292e-4`;
  - `Kylin-256-q24`: `h=21,d=1,h_vec=[21], BPORS=(3,14,3072,8,202), w=6, len=102, sig=11208`, `bitsec=255.587871`, `tau=1.17726968272e-4`;
  - `Kylin-512-q24`: `h=41,d=2,h_vec=[20,21], BPORS=(7,15,224,10,336), w=12, len=145, sig=47240`, `bitsec=511.191929`, `tau=1.21683287616e-4`.
- 已同步：`paper/data/para_kylin_final_6profiles.csv`、`para_kylin_selected_6profiles.csv`、12 个实现目录 `params.h`、`AGENTS.md`、`Implementations/README`、英文/中文参数表、安全表、性能 hashcall 表、q24 附录、KAT 摘要表、impact note 与术语表。
- KAT 刷新完成：六个 `Test_Vectors/KAT_SIG_Kylin-*.txt` 均为 120 行；q24-512 长任务使用临时单 count 拆分生成器并行完成，临时 count00/count01 与官方 `make kat` 已生成的 count 0/1 字节级一致后合并。最终 SHA-256：
  - `Kylin-128`: `db4b95738e79df45ab20e06a768eec576d70712ef4962a7936b1344dbfa57db7`;
  - `Kylin-256`: `141bb7daee612f22bdd18a1d9fe7868c78434308dc7ecc86ae107e3ea9a0f1bc`;
  - `Kylin-512`: `2c16f6190028eff55db3a7f2aff00c7b51098378759381fd2c43e1b7bafd38ed`;
  - `Kylin-128-q24`: `c284b49d8cf9075a513878a2c68535ae08a9236fe2f713b90d086268e6ddd46c`;
  - `Kylin-256-q24`: `5cc6cf82cc4399d990eba8577de32dede7620fd1daa4c4b5defd869c73de748d`;
  - `Kylin-512-q24`: `d5529d69487b37eb237d6f936e5db62dace4c7e4b94a8afada547146e6a52e50`.
- 验证：`python3 -m py_compile paper/code/search_sphincs_compare_params.py paper/code/search_bpors_kylin_params.py paper/code/check_bpors_profiles.py` 通过；`python3 paper/code/check_bpors_profiles.py --q24-tau-floor 1e-4` 通过；`git diff --check` 通过；`make -C paper/build all` 与 `make -C paper/build zh` 均通过。主提交 Reference/Optimized 三档 `make clean all test` 已在本轮参数同步后通过，包括 `Kylin-512`；q24-128 Reference `make clean all test` 与 q24 optimized KAT 路径通过，q24-512 完整 KAT 已由每个 count 内部 sign+verify 验证。

### 2026-06-26 - Parameter Residue Audit and Cleanup (Done)

- 检查当前参数源、实现 `params.h`、论文源码、PDF 文本、默认参数脚本入口和辅助表格，发现并清理两类真实残留：`paper/data/para_ngcc_table*.csv` / `paper/tex/submission_overview.tex` 仍使用旧 FORS 表头与旧三档主参数；`paper/code/para.sage` 作为附录代码仍输出旧 FORS tuple。
- 将 `para_ngcc_table*.csv` 与 submission overview 表改为当前 BPORS+FP 主提交 rows；将 `paper/code/para.sage` 重写为读取 `paper/data/para_kylin_final_6profiles.csv` 的 BPORS+FP checker，重新计算签名长度、BPORS cover bitsec 与 sign/verify hashcall。
- 修正默认参数入口：顶层 `make params` 改为运行 `check_bpors_profiles.py --q24-tau-floor 1e-4`；`paper/code/search_ngcc_params.py` 默认输出当前 q64 BPORS+FP rows 且不再无意写回旧 `para_ngcc.csv`；`paper/code/search_bpors_kylin_params.py` 的 `CURRENT_BPORS_UPPER` 与 `SECURE_BPORS_FALLBACKS` 同步到最终六组参数，显式 `FORS_BASELINES` 保留为历史基准。
- 将 `paper/build/Makefile` 的英文/中文构建依赖补充 `paper/code/*`，避免 minted 附录代码变化后 PDF 不重建；`new-files/kylin_security_proof.tex` 标注为未参与当前构建的 FORS-era historical draft，当前维护入口指向 `paper/tex/security_statements_and_analyses.tex` 与最终 CSV。
- 验证：`python3 paper/code/para.sage`、`python3 paper/code/search_ngcc_params.py`、`make params`、`python3 paper/code/check_bpors_profiles.py --q24-tau-floor 1e-4`、12 个 `params.h` 对最终 CSV 的结构比对、`make -C paper/build all`、`make -C paper/build zh`、`make -C paper/build zh` up-to-date 检查、`git diff --check` 均通过；`pdftotext` 抽查确认英文/中文 PDF 附录已显示当前 BPORS+FP 参数。当前 active 源码扫描仅剩 `FORS_BASELINES`、`para_ngcc.csv`、`para_fors_baseline_6profiles.csv`、candidate CSV 与 `plan.md` 历史记录中的旧值，均为显式历史/基准材料。

### 2026-06-26 - Paper TBD and Placeholder Cleanup (Done)

- 扫描 `main.tex`/`main_zh.tex`、`paper/tex*`、`paper/data` 与 PDF 文本，确认 active PDF 中真实暴露的待补项是 performance evaluation 的 package benchmark 表；`submission_overview.tex` 与 `submission_checklist.tex` 未被 `main.tex` 引入，但也含有旧 TODO/placeholder wording。
- 运行 `python3 Implementations/tools/collect_metrics.py` 完成主提交 Reference/Optimized 六个实例的 package metrics，填充 `paper/data/package_bench.csv`、`paper/data/package_memory.csv` 与 `Implementations/benchmarks/summary.md`。本次本机中位数 benchmark 包括 `Kylin-128 opt/ref = 871.313/1746.791 ms sign`、`Kylin-256 opt/ref = 997.808/2322.339 ms sign`、`Kylin-512 opt/ref = 21804.592/36862.925 ms sign`。
- 更新英文/中文 performance section：删除 `TBD`/`待定` 说明，写明时间为 32-byte message 上 3 次 warmup 后 9 次测量的 median；同步清理 q24 附录中的 `legacy-target` wording。
- 修正文稿中顺手发现的严谨性/表述问题：WOTSCS `wots_pkFromSig` 不再描述为使用 message checksum，而改为 constant-sum base-$w$ encoding values；修复 `stings`、`sum ... is equals`、HT 描述断句与 footnote 中的 `can assumed`；将 “draft/本草稿” wording 改为 specification/本规范。
- 将未引入的 submission overview/checklist 草稿改为完成态外部材料引用，移除红色 `\todo{}` 内容，并同步为当前 CSV 中的主参数高度 `{62,65,64}`。
- 验证：`make -C paper/build all`、`make -C paper/build zh` 均生成 PDF；英文 build 仍出现 WSL/Windows clock-skew 环境警告和既有 overfull/underfull 排版警告，中文 build 有既有字体替代与 overfull 警告，但均退出成功。`pdftotext` 扫描 `main.pdf` 与 `main_zh.pdf` 未再发现 `TBD`、`TODO`、`FIXME`、`待定`、`legacy-target`、`this draft`、`本草稿` 等正文占位符；源码扫描仅剩 `defs.tex` 中的宏定义名、`docs/API_PKC` 模板中的 `XXX_AlgorithmInstance` 与 `plan.md` 历史记录；`git diff --check` 通过。

### 2026-06-29 - Paper Consistency Fixes for Algorithm Text PDF (Done)

- 修正论文审查中标出的 1/2/3/6 项：将中文 \WOTSCS 目标消息空间与链长条件从 `2^n`/`\bool^n` 改为 `2^{8n}`/`\bool^{8n}`；将英文/中文 Table 1 的 sign/verify hashcall 更新为当前 sampler-cost model 下的 `2113169/2062`, `2912474/4312`, `11566745/16757`；将英文/中文 construction 中的 `\mathcal{M}=[w]^{l_l}` 修正为 `\mathcal{M}=[w]^{l_1}`。
- 重新构建 `main.pdf` 与 `main_zh.pdf`。由于当前 shell 解析到的大写路径位于只读挂载，构建中间产物放在 `/tmp/kylin-texout`，随后同步回仓库根目录与 `paper/build/out`。
- 用新 `main.pdf` 覆盖根目录 `算法文本.pdf` 与 `build/算法文本.pdf`；当前 `main.pdf`、`算法文本.pdf`、`build/算法文本.pdf`、`paper/build/out/main.pdf` 的 SHA-256 均为 `c5836a9e16925f59835e7fd3447fcaecb024f777b9ee5a29025ddfde8a9b1195`。
- 验证：源码扫描不再发现上述旧公式/旧 hashcall/`l_l`；`pdftotext` 抽查确认 `算法文本.pdf` 中 Table 1 与 performance table 均为新 hashcall 且旧参数残留消失；最终 `main.log`/`main_zh.log` 无未解析 citation/reference 错误，仅保留既有中文字体替代与 overfull/underfull 排版警告。

### 2026-06-30 - Paper Intro, Proof, Grammar, and Layout Polish (Done)

- 修正英文/中文引言中的旧叙述：当前主线明确为 \WOTSCS、BPORS+FP 和 diverse layer heights 三项改动；不再声称修改仅限于 WOTS 编码和超树层高。
- 补强 Kylin reduction theorem 证明说明：解释左填充 BPORS+FP 子树的 `<2t` 哈希节点上界、外层桶树节点的 slack 覆盖，以及 XMSS 节点如何被吸收到保守的 `q_4 < 2^{h+1}K2^B(2t+2)` 目标计数中；同步更新中文镜像。
- 修正 construction 中的英文语病和长行：`message-signature pair`、`reaches its maximum`、`element increases`，并将若干行内公式改为展示公式；缩短 `wots_pkFromSig` 小节标题和 q24 appendix 优化实现说明以清除 overfull。
- 同步处理中文镜像中的对应排版问题：拆分长公式/长段落，修正 q24 appendix 的长行说明，并保持英文源为主、中文结构跟随。
- 验证：`make -C paper/build all` 与 `make -C paper/build zh` 均通过；英文/中文日志无未解析 citation/reference、无 `Overfull`；英文仅剩 bibliography underfull，中文仅剩环境字体替代提示。已用新 `main.pdf` 覆盖根目录与 `build/` 中的 `算法文本.pdf`，当前 `main.pdf`、`算法文本.pdf`、`build/算法文本.pdf`、`paper/build/out/main.pdf` 的 SHA-256 均为 `bbca23b5488bac8cbb7317c1d4c98689b52cea27b5112757a8433ffc9c8d1e22`。
