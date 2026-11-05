<!-- @author Pjh -->
# 可运行的协议示例

在完整仓库根目录执行 `python3 examples/run_demo.py`。程序使用 Python 标准库，在启动目录的 `.codex/verification/demo-时间/` 下保存每次运行结果。

示例依次生成两个独立运行目录：

1. `self`：写入合成文件并使用 schema 4 自检记录，预期 CLI 退出码为 1，状态为 provisional。
2. `changed`：替换合成文件正文，使已声明主张的引文消失，预期 CLI 退出码为 1，状态为 partial。

示例程序确认这两个预期状态后，自身以退出码 0 结束。复现某次结果时，使用该目录 `invocation.json` 中的精确命令。示例与协议回放均使用合成输入，其中的评审身份标签属于测试数据。

准备真实任务的 CLI 输入时，按[输入协议](../skills/work-eval/references/record-checking-protocol.md)填写实际要求、工件、来源及评审结果。
