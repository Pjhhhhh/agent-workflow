<!-- @author Pjh -->
# pstack 现状与本机适用性

核查日期：2026-10-10。上游固定为 Cursor plugins 的提交 `ccb5507cec1546dc88135c1139c811e6c59115ba`，提交时间为 2026-10-08 00:45:14 UTC；pstack manifest 版本为 **0.15.15**，作者为 Lauren Tan，许可证为 MIT。本文只核查上游源码、文档和本机只读状态，没有安装插件、改配置或运行 pstack。静态可适配不等于运行通过。[固定提交](https://github.com/cursor/plugins/commit/ccb5507cec1546dc88135c1139c811e6c59115ba)、[manifest](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/.cursor-plugin/plugin.json)

1. **它是什么。** pstack 是一套 Cursor 工程技能与子代理工作流。`poteto-mode` 接收任务，选择 23 个 playbook 之一，再调用理解、设计、实现、评审和验证技能；24 条原则要求真实行为证据、可验证的小单元和明确的数据结构。它也包含 PR 跟进、合并、长期自治等流程。作者的质量与并行收益描述是设计主张，本文没有效果对照数据。[README](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/README.md)、[poteto-mode](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/skills/poteto-mode/SKILL.md)

2. **短提示为何有用。** 当前指南确有“重试后收到两条通知，先复现再修复验证”的例子。它建议最多交代五项：目标、可判定的完成条件、证据、已知线索和约束。短提示背后有 playbook 承担步骤；普通自然语言也能表达这些要求，`/poteto-mode` 不是本机会话中已确认可用的 Codex 命令。[提示指南](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/docs/guide/02-poteto-mode.md)

3. **本机能否使用。** 本机 Codex CLI 为 0.162.0；在 `/Applications`、`~/Applications` 和命令路径中未发现 Cursor，`~/.cursor` 不存在。本地插件缓存、技能路径及当前会话目录未发现 pstack。`codex plugin list --json` 退出成功，但远端 catalog 请求失败，因此结论限于已检查的本地范围。Codex 官方支持 `SKILL.md` 技能、根目录 portable `plugin.json` 与 `.codex-plugin` manifest 回退；当前 pstack 使用 `.cursor-plugin/plugin.json`。现有证据支持移植技能内容，不能证明 Cursor 原包可直接加载或整套运行。[Codex 插件结构](https://developers.openai.com/plugins/build/plugins)、[Codex 技能](https://developers.openai.com/plugins/concepts/skills)、[pstack manifest](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/.cursor-plugin/plugin.json)

4. **是否值得安装。** 对当前 Codex 工作区，建议继续吸收具体方法，暂不整套安装。下表中的宿主依赖与权限差异需要先适配；已有 work-eval 又覆盖了重要验证要求。上游也建议从重复失败处增补技能，无需一开始采用整个插件。这是基于依赖与本机流程的判断，尚未比较安装前后的质量、返工或成本。[从小处开始](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/docs/guide/09-make-it-yours.md)

| 核查对象 | 上游实际要求 | 本机适用边界 |
| --- | --- | --- |
| 技能与模型配置 | `/setup-pstack` 写 `~/.cursor/rules/pstack-models.mdc`，新会话生效；模式通过 Cursor `Task`、`poteto-agent` 和角色模型委派 | 必须换成本机技能入口、子代理接口和可用模型；写了 Cursor 规则不证明 Codex 会读取。来源：[setup](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/skills/setup-pstack/SKILL.md)、[子代理](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/agents/poteto-agent.md) |
| 完整集成 | `deslop`、`control-cli`、`control-ui` 来自另一个 `cursor-team-kit` 插件；`create-skill` 与 `/loop` 是 Cursor 内建能力 | 需复用本机已有工具或实现替代入口；仅复制 pstack 不齐备。来源：[外部依赖](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/README.md#not-shipped-here)、[自治运行](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/skills/poteto-mode/playbooks/autonomous-run.md) |
| verify | 生成项目本地 Launch、Doctor、Drive、Evidence、Cleanup 与 Feature Map；交付前实际驱动一个功能，维护时逐功能源码核查及实测 | 方法适用；具体路径、启动条件与权限按项目决定，生成文稿不等于已验证。来源：[生成](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/skills/create-verification-skill/SKILL.md)、[维护](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/skills/maintain-verification-skill/SKILL.md) |
| hooks 与脚本 | 该提交的 pstack 文件树和 manifest 未见 hook 注册；另有 Bun 工具，bootstrap 可自动安装依赖 | 不能称其已提供 Codex Stop 门禁；执行脚本也不等于只读技能。来源：[固定目录树](https://github.com/cursor/plugins/tree/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack)、[bootstrap](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/skills/poteto-mode/scripts/bootstrap.ts) |
| 自治与发布 | 模式允许团队聊天、工单等外部动作；部分 playbook 包含提交、推送、PR、云代理验证及合并 | 本项目禁止自动 Git 修改；发送、安装、删除、发布仍受本轮授权约束。上游文字不扩大权限。来源：[自治范围](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/skills/poteto-mode/SKILL.md)、[shipping](https://github.com/cursor/plugins/blob/ccb5507cec1546dc88135c1139c811e6c59115ba/pstack/skills/poteto-mode/playbooks/shipping.md)、[项目规则](../AGENTS.md) |

已有借鉴可以从现存记录确认。[流程参考与取舍](流程参考与取舍.md)记录了 2026-09-30 的 pstack 0.15.5／`fae2c6ed95821bd85f614a73e4842e13229fa5e5`，列明 Feature Map、验证工具、证据分类、举证评审和恢复原工件等做法；[现行工作流](../skills/work-eval/SKILL.md)、[功能入口](../skills/work-eval/references/features.md)、[防编造与范围核查](../skills/work-eval/references/safety.md)仍包含对应要求。这证明本地文档明确记录过借鉴及当前采用方式，不能推出每条规则都源自 pstack，或这些规则已降低模型编造率。

当前可直接采用的提示例子：修复重试导致的重复通知；先复现，完成条件是一次重试只发一条通知且正常交付仍有效；展示修复前失败与修复后通过的证据，交付可审查的差异，Git 写入按当前授权处理。下一次若要评估新增技能，优先选择一个已有失败任务，在隔离范围内适配一个验证入口，比较证据完整性、漏项、返工和成本。插件加载、模型委派、真实应用驱动、成本收益及热加载均未验证。
