# 文档索引

本目录保留原始 PDF，并提供人工整理后的 Markdown 版本。

| 原始文件 | Markdown |
| --- | --- |
| [公钥密码算法提交要求.pdf](公钥密码算法提交要求.pdf) | [公钥密码算法提交要求.md](公钥密码算法提交要求.md) |
| [公钥密码算法评估准则.pdf](公钥密码算法评估准则.pdf) | [公钥密码算法评估准则.md](公钥密码算法评估准则.md) |
| [对于公钥密码算法提交要求与评估准则相关意见的反馈.pdf](对于公钥密码算法提交要求与评估准则相关意见的反馈.pdf) | [对于公钥密码算法提交要求与评估准则相关意见的反馈.md](对于公钥密码算法提交要求与评估准则相关意见的反馈.md) |
| [Submission Requirements for Public-Key Cryptographic Algorithms.pdf](Submission%20Requirements%20for%20Public-Key%20Cryptographic%20Algorithms.pdf) | [Submission Requirements for Public-Key Cryptographic Algorithms.md](Submission%20Requirements%20for%20Public-Key%20Cryptographic%20Algorithms.md) |
| [Evaluation Criteria for Public-Key Cryptographic Algorithms.pdf](Evaluation%20Criteria%20for%20Public-Key%20Cryptographic%20Algorithms.pdf) | [Evaluation Criteria for Public-Key Cryptographic Algorithms.md](Evaluation%20Criteria%20for%20Public-Key%20Cryptographic%20Algorithms.md) |
| [Feedback on the Comments Received on the Draft Submission Requirements and Evaluation Criteria for Public-Key Cryptographic Algorithms.pdf](Feedback%20on%20the%20Comments%20Received%20on%20the%20Draft%20Submission%20Requirements%20and%20Evaluation%20Criteria%20for%20Public-Key%20Cryptographic%20Algorithms.pdf) | [Feedback on the Comments Received on the Draft Submission Requirements and Evaluation Criteria for Public-Key Cryptographic Algorithms.md](Feedback%20on%20the%20Comments%20Received%20on%20the%20Draft%20Submission%20Requirements%20and%20Evaluation%20Criteria%20for%20Public-Key%20Cryptographic%20Algorithms.md) |

## 转换说明

- 清理了 PDF 页码、目录点线、强制换行和多余空白。
- 按原文结构重建标题层级、列表、代码块和表单表格。
- 将 PDF 文本抽取中丢失的上标整理为 `2^n`、`2^63`、`2^64`、`2^80` 等写法。
- `API_PKC.zip` 及其解压出的示例接口文件保持原样。

## 仓库实现布局更新（2026-04-26）

- `q=2^24` 的三组实现（`Kylin-128-q24`、`Kylin-256-q24`、`Kylin-512-q24`）已从主实现目录转入 `Implementations/Additional_Implementation/`。
- `Additional_Implementation` 不再区分 `Reference_Implementation` 与 `Optimized_Implementation` 子目录，当前仅保留 Ref 版本目录：`Implementations/Additional_Implementation/Kylin-*-q24`。
- 主提交实现目录保留 `q=2^64` 的三组：`Kylin-128`、`Kylin-256`、`Kylin-512`。
