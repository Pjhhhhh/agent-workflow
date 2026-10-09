<!-- @author Pjh -->
# agent-workflow

让 AI 代理围绕用户要求完成工作，并用实际结果验收。适用于代码开发、文档填写、电脑操作和资料研究。

核心技能是 **work-eval**：简单任务直接核验；复杂任务固定必要要求、独立评审、逐项检查，发现可修的缺口就回到执行。图集按需查看，不是使用前提。

## 安装

使用支持 Agent Skills 的安装器，选择目标客户端与安装范围：

```sh
npx skills add Pjhhhhh/agent-workflow --skill work-eval
```

也可以把 `skills/work-eval` 整个目录复制到客户端的技能目录。技能包含自己的脚本和参考资料，不依赖仓库外层文档。脚本需要 Python 3.9+，只使用标准库；安装器需要 Node.js，手动复制不需要。

## 使用

在 Codex 中显式调用 `$work-eval`，或要求代理读取已安装技能：

> 使用 work-eval 完成这项任务，核对原始要求和最终工件；有可修的验收缺口就继续，完成后给出结果与验证证据。

希望成为默认工作方式时，把下面这段合并到自己的代理规则中，保留原有项目与权限约定：

> 处理代码、文档、电脑操作和资料研究时，读取 work-eval 技能并按其分支执行。纯问答直接回答，简单任务直接核验，复杂任务独立评审并逐项验收。记录留在实际工作区，遵守目标项目的权限和测试约定。

安装不会自动修改 AGENTS.md、接入全局hooks或授予额外操作权限。详细步骤、源码链接安装和重启要求见[安装与更新](docs/安装与更新.md)。

## 按需搭配 Matt Pocock

`work-eval` 负责执行范围和结果验收；[Matt Pocock Skills](https://github.com/mattpocock/skills) 可用于工程任务中的诊断、拆分、实施和代码审查。代理按任务读取适用的已安装技能，不要求每次走完一套阶段。

首次使用时，可以按需安装下面这些技能，并在安装器中选择客户端与安装范围；已经安装的直接复用：

```sh
npx skills@latest add mattpocock/skills --skill setup-matt-pocock-skills diagnosing-bugs to-tickets code-review ask-matt
```

示例不包含 `implement`，避免覆盖已有的自管版本。若另选上游 `implement`，其测试和提交步骤仍须遵守目标项目的有效约定与用户授权。首次项目配置、按任务选择和本地版本保护见[安装说明](docs/安装与更新.md#可选matt-pocock工程技能)与[接入规则](skills/work-eval/references/matt-pocock.md)。

## 技能内容

| 文件 | 作用 |
| --- | --- |
| [SKILL.md](skills/work-eval/SKILL.md) | 执行分流、验证、回修与交付 |
| [rubric.md](skills/work-eval/references/rubric.md) | v3契约和评审输入格式 |
| [safety.md](skills/work-eval/references/safety.md) | 来源、范围、模板格式和恢复核查 |
| [features.md](skills/work-eval/references/features.md) | CLI入口与记录行为 |
| [work_eval.py](skills/work-eval/scripts/work_eval.py) | 确定性的记录、引文、版本和声明操作检查 |

验收结果为 `pass`、`fail`、`partial` 或 `provisional`；不使用五维总分。自检不会变成独立通过，工件变化后旧判断不能直接沿用。

## 示例与验证

下载完整仓库后，在根目录运行：

```sh
python3 examples/run_demo.py
python3 scripts/verify_protocol.py
```

[合成示例](examples/README.md)展示自检与版本失效，协议回放覆盖119项，包括单独安装技能后的运行和门禁隔离。记录写入启动目录 `.codex/verification/`。版本与验证边界见[验证摘要](docs/验证摘要.md)。

当前为实验版。独立评审仍可能漏项，脚本不能证明来源支持结论、操作记录完整或评审身份真实。没有通用业务执行器、跨轮自动恢复器或全局强制门禁；模型完成率和成本改善尚未进行对照验证。

## 文档

- [工作流程](docs/工作流程.md) · [流程图集](docs/diagrams/index.html)
- [已知问题](docs/问题与失败清单.md) · [真实任务检验](docs/真实任务检验.md)
- [维护说明](docs/维护说明.md) · [参考与取舍](docs/流程参考与取舍.md)

仓库结构参考 [Matt Pocock Skills](https://github.com/mattpocock/skills) 与 [Anthropic Skills](https://github.com/anthropics/skills)：README提供入口，技能目录自包含，额外说明按需阅读。本项目只有一个核心技能，不引入无关插件或多包框架。

## 许可

项目自有内容采用[MIT许可](LICENSE)。图集的第三方和内嵌字体声明见[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。私人计划、业务材料、会话、配置和浏览器日志不随仓库提交。
