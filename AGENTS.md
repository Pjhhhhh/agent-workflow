<!-- @author Pjh -->
# agent-workflow 流程维护

本项目是通用默认 AI 工作流程的源码维护目录，图集用于按需说明，Stop 接口仍是局部实验。用户级 `~/.agents/skills/work-eval` 链接到本项目的 `skills/work-eval`；其他项目不依赖图集。规则适用于以项目根目录或其子目录为工作区的新建、恢复及继续中的会话。项目根由 `.agent-workflow-root` 标记；规则、技能和脚本路径均相对项目根解释。

接手实质任务先读 [默认工作流技能](skills/work-eval/SKILL.md)，按其唯一分流标准执行；纯问答、状态查询和没有实质工作的流程讨论不生成验收记录。执行或评审流程时读 [防编造与范围核查](docs/防编造与范围核查.md)。安装、Git 写入、外部发布和门禁实验仍按当前授权，不接入全局 hooks 或角色。

接手时刷新当前项目规则；恢复未完成任务按 [任务跟踪约定](docs/agents/issue-tracker.md) 定位原计划、有效要求和下一动作。规则文件修改不证明已运行会话或所有宿主已经加载；不能把其他会话的目标和授权自动带入。

修改验收协议前在 [问题与失败清单](docs/问题与失败清单.md) 记录风险，再用 `scripts/verify_protocol.py` 黑盒回放。入口、验证及历史证据见 [维护说明](docs/维护说明.md)。修改图源后使用 Archify validate、deliver、visual-check，保留实际浏览器证据；原始规则和图源不保存私人会话或配置。

## Agent skills

- 拆分、读取或更新任务：先读 [任务跟踪约定](docs/agents/issue-tracker.md)，新计划统一放项目根 `.plan/`，旧记录不搬迁。
- 任务分诊：使用 [五个默认标签](docs/agents/triage-labels.md)。
- 领域探索或架构决策：先读 [领域文档约定](docs/agents/domain.md)，采用根 `GLOSSARY.md` 与 `docs/adr/`。
