# Kylin Submission EN->ZH Glossary

This glossary fixes the preferred wording for the bilingual submission document so later English updates can be mirrored into Chinese without re-deciding terminology.

## Core Rules

- English remains the source of truth.
- Keep formulas, labels, citation keys, code identifiers, instance names, CSV paths, and file paths unchanged.
- Translate prose, headings, captions, theorem-like names, TOC/list labels, and cross-reference names.
- Prefer consistency over literary variation when the same technical phrase appears multiple times.

## Preferred Terms

| English | Chinese | Notes |
| --- | --- | --- |
| hash-based signature | 基于哈希的签名 | Generic family name. |
| stateful signature | 有状态签名 |  |
| stateless signature | 无状态签名 |  |
| one-time signature | 一次性签名 |  |
| few-time signature | 少次签名 |  |
| bucket thinning | bucket thinning（桶稀疏） | Keep English term on first use when naming the technique. |
| BPORS+FP | BPORS+FP | Do not translate component acronym. |
| forced pruning | forced pruning | Keep English technical term; explain as `强制剪枝` only if needed. |
| forced-pruning acceptance probability | forced-pruning 接受概率 | Table/checker prose can use `tau` unchanged. |
| counter | counter | Keep English in BPORS+FP algorithm prose and code-facing descriptions. |
| Octopus authentication set | Octopus 认证集合 | Keep `Octopus` unchanged. |
| hypertree | 超树 | Keep `HT` token unchanged when used as an algorithm/component name. |
| layer height | 层高 | `layer heights` -> `分层高度`. |
| Diverse Layer Heights | Diverse Layer Heights（分层高度多样化） | First use can keep English plus Chinese. |
| address scheme | 地址方案 |  |
| hash-call proxy | 哈希调用代理计数 | For document tables and performance discussion. |
| key generation | 密钥生成 |  |
| signing | 签名 | Verb or noun by context. |
| verification | 验证 |  |
| signature size | 签名大小 | `signature bytes` can be `签名字节数`. |
| public key | 公钥 |  |
| secret key | 私钥 | Do not rename macro tokens `PK` or `SK`. |
| parameter set | 参数集 |  |
| packaged instance | 已打包实例 | Used for the frozen NGCC-facing instances. |
| frozen parameter set | 冻结参数集 |  |
| reference implementation | 参考实现 |  |
| optimized implementation | 优化实现 |  |
| additional implementation | 附加实现 | For the companion `q=2^24` implementation track. |
| security statement | 安全性声明 |  |
| security analysis | 安全性分析 |  |
| security model | 安全模型 |  |
| proof outline | 证明主线 | Use for concise proof-structure prose. |
| game proof | game 证明 | Keep `game` in English when referring to game-hopping proof steps. |
| reduction theorem | 归约定理 |  |
| single-instance | 单实例 |  |
| multi-instance | 多实例 |  |
| constant-sum antichain | 常和反链 |  |
| target-collision resistance | 目标碰撞抗性 |  |
| preimage resistance | 原像抗性 |  |
| undetectability | 不可检测性 |  |
| decisional second-preimage resistance | 判定型第二原像抗性 |  |
| interleaved target subset resilience | 交错目标子集韧性 | Keep `ITSR` token unchanged. |
| generic attack | 通用攻击 |  |
| bit security | bit-security | Keep English technical phrase in formulas/tables. |
| design rationale | 设计依据 |  |
| performance evaluation | 性能评估 |  |
| feature statements | 特性说明 |  |
| theorem | 定理 |  |
| lemma | 引理 |  |
| corollary | 推论 |  |
| proposition | 命题 |  |
| definition | 定义 |  |
| algorithm | 算法 |  |
| table | 表 |  |
| figure | 图 |  |
| appendix | 附录 |  |

## Tokens That Should Stay in English

- `Kylin-128`, `Kylin-256`, `Kylin-512`
- `Kylin-128-q24`, `Kylin-256-q24`, `Kylin-512-q24`
- `SPHINCS+`, `CS-WOTS+`, `WOTS+`, `XMSS`, `BPORS+FP`, `FORS`, `HT`
- `SIG_AlgorithmInstance.h`, `SIG_AlgorithmInstance.c`, `KAT_SIG.c`
- `pseudoXOF`, `pseudohash`, `sm3hash`
- `paper/data/para_kylin_final_6profiles.csv`

## Style Notes

- Prefer `尺寸` for generic size discussion and `字节数` for exact table-column wording.
- Translate `tradeoff` as `折中`, not `权衡`, to stay aligned with existing English paper phrasing.
- When a component has a stable acronym, translate the surrounding prose but keep the acronym itself.
- On first use of a paper-specific optimization term, it is acceptable to keep the English name followed by a Chinese gloss in parentheses.
