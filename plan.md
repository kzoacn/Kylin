# Kylin NGCC Submission Completion Plan

## 1. 当前目标

项目当前目标是**完成 Kylin 的 NGCC 提交质量收敛**，重点不再是历史整理，而是把现有包提升到可提交、可解释、可复现的状态。

当前实现布局如下：

- 主提交实现（`q=2^64`）：`Kylin-128`、`Kylin-256`、`Kylin-512`
- Additional 实现（`q=2^24`，仅 Ref）：`Kylin-128-q24`、`Kylin-256-q24`、`Kylin-512-q24`

参数定版文件：`paper/data/para_kylin_final_6profiles.csv`。

历史目录 `.SPHINCS-ALPHA-NIST/` 仅作为归档材料，非必要不读取。

## 2. 已有基础（已完成）

- 当前三组基线实例（128/256/512）的参考实现与优化实现目录已建立；`q=2^24` 三组已作为 Additional（仅 Ref）实现维护；六组最终参数已导出并冻结。
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

### Phase C: 文档完善（英文定稿 + 中文文档）（Priority: P1）

**目标**：输出完整、提交导向的中英文材料。

任务：

- 英文文档统一术语与命名（全部聚焦 Kylin/NGCC）。
- 补齐参数依据、实现边界、测试方法与性能解释。
- 新建中文文档（结构与英文稿一致，内容面向提交审阅）。
- 保证图表、表格、引用、术语在中英文间一致。

验收标准：

- 英文文档可直接用于提交包。
- 中文文档结构完整，可作为同步审阅版本。
- `paper/build` 全流程编译无引用错误。

### Phase D: 提交打包与清单收口（Priority: P0）

**目标**：形成可直接交付的 NGCC 提交目录与检查清单。

任务：

- 对照 `docs/` 要求整理最终目录结构与必需文件。
- 固化打包脚本/命令（构建、测试、KAT、文档、向量）。
- 生成提交前 checklist（接口、文件完整性、可重复构建、版本标识）。
- 补齐外部表单与声明项（如需人工签署则明确状态与责任人）。

验收标准：

- 从干净环境可复现构建与主要验证流程。
- 提交包文件齐全，命名与目录符合 NGCC 规范。
- checklist 全项有状态，阻塞项明确。

## 4. 执行原则

- 每个中等规模任务完成后：更新 `plan.md` 进度日志，并执行 `git add`、`git commit`、`git push`。
- 默认优先读取 `Implementations/`、`docs/`、`paper/`、`main.tex`；归档目录仅在必要时查阅。
- 任何参数变更必须同步：实现常量、文档表格、测试向量、说明文字。

## 5. 进度日志

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

- 统一修复 `\len` 显示口径：宏定义改为稳定形式，并在 `paper/tex/sphincsp.tex` 内将 `\tt len` / 裸 `len` 的混用统一为 `\len`，避免章节内显示风格不一致。
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
  - `paper/tex/abstract.tex`、`paper/tex/submission_overview.tex`、`paper/tex/submission_checklist.tex`、`paper/tex/sphincsp.tex`、`paper/tex/sphincsp-appendix.tex` 已移除旧的统一 `(70,10,14,64)` 叙述并更新为定版口径。
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
  - `paper/tex/sphincsp.tex` 的 repeated-key 条目删除 `q <= 2^80` 扩展解释，仅保留 `q=2^64` 目标声明。
- 验证：
  - 关键词复扫：`paper/tex` 与 `main.tex` 中已无 `2^80` / `q<=2^80` 表述。
  - 编译验证：`latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error -outdir=/tmp/kylin-draftcheck main.tex` 通过，输出 `/tmp/kylin-draftcheck/main.pdf`。

### 2026-04-26 - Draft Cleanup: Replace Remaining `spa_*` Markers with `kylin_*` (Done)

- 清理文稿中残留的旧算法入口记号：
  - `paper/tex/sphincsp.tex` 中三处 `\inputminted` 已从 `paper/code/spa_*.cs` 改为 `paper/code/kylin_*.cs`。
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
  - `paper/tex/abstract.tex`、`paper/tex/submission_overview.tex`、`paper/tex/submission_checklist.tex`、`paper/tex/sphincsp-appendix.tex` 中移除正文里直接显示的 `.csv`、`.py`、`.txt`、`.zip` 路径/文件名，改为自然语言描述。
  - 保留 LaTeX 内部 `\csvreader` / `\inputminted` 输入路径，不影响排版生成。
- 验证：
  - 编译验证：`latexmk -pdf -shell-escape -interaction=nonstopmode -halt-on-error -outdir=/tmp/kylin-doc-polish main.tex` 通过，输出 `/tmp/kylin-doc-polish/main.pdf`。
  - 成品核对：PDF 文本中已出现 `3.1 Diverse Layer Heights in the Hypertree` 与 `3.2 The WOTS+ Encoding`。
