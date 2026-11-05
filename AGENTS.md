<!-- @author Pjh -->
# agent-workflow 流程维护

本项目维护通用 AI 工作流程的源码、技能和说明，图集解释历史流程与局部实验，Stop 接口用于局部实验。用户级 `~/.agents/skills/work-eval` 链接到本项目的 `skills/work-eval`。规则适用于以项目根目录或其子目录为工作区的新建、恢复及继续中的会话。项目根由 `.agent-workflow-root` 标记；规则、技能和脚本路径均相对项目根解释。

通用行为和表达遵守宿主当前有效的全局规则。实质任务读取[默认工作流技能](skills/work-eval/SKILL.md)，按其分流执行与核验；纯问答、状态查询和流程讨论直接回答。执行或评审流程时按需读[防编造与范围核查](docs/防编造与范围核查.md)。安装、Git 写入、外部发布和门禁实验按当前授权执行；全局 hooks 和角色配置需要专项授权。

本项目提交前若选择 OCR，按 [OCR 审查说明](skills/work-eval/references/optional-integrations.md#open-code-review模式选择) 审查本次必要范围内全部可处理文件。必要问题已解决，必要审查、功能验证和验收通过且证据齐备后，按 [Git 提交与推送范围](skills/work-eval/references/execution-and-recovery.md#git-提交与推送范围) 执行各自已获授权的操作。代码、规则及相关证据未变化且未受影响时，复用有效结果。

接手时刷新当前项目规则；恢复未完成任务按 [任务跟踪约定](docs/agents/issue-tracker.md) 定位原计划，核对本次有效要求、授权和下一动作。规则更新后，让相关会话重读受影响内容。

修改验收协议前在 [问题与失败清单](docs/问题与失败清单.md) 记录风险，再用 `scripts/verify_protocol.py` 黑盒回放。入口、验证及历史证据见 [维护说明](docs/维护说明.md)。修改图源后使用 Archify validate、deliver、visual-check，保留实际浏览器证据；公开的规则和图源使用脱敏材料。

维护者本机默认按职责选模型：Astra（`gpt-6-astra`）负责分析、方案和独立复审，GPT-6.1-Sol（`gpt-6.1-sol`）、`xhigh` 负责实际修改和执行验证。当前会话符合职责时直接承担；需要委派且宿主支持模型选择时，传入明确模型和推理参数，调用失败时说明具体缺口。

## Agent skills

- 创建、读取或更新任务：先读 [任务跟踪约定](docs/agents/issue-tracker.md)，新计划统一放项目根 `.plan/`，旧记录保留原处。
- 任务分诊：使用 [五个默认标签](docs/agents/triage-labels.md)。
- 领域探索或架构决策：先读 [领域文档约定](docs/agents/domain.md)，采用根 `GLOSSARY.md` 与 `docs/adr/`。
- 文档任务：读取宿主规则指定的文档规范，并使用[文档编写与维护技能](skills/doc-maintenance/SKILL.md)。
