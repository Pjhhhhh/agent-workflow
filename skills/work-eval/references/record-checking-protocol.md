<!-- @author Pjh -->
# 显式记录检查协议

选用 `score` 检查结构化记录时，新输入使用 schema 4，包含任务要求文件和评审 JSON。脚本核对提交的记录、当前工件、正文引文及声明操作；评审者核对来源是否支持结论、操作是否获准，以及实际结果是否满足要求。

检查状态、恢复动作和旧版输入的处理见[检查状态与恢复](#检查状态与恢复)。日常任务按[默认技能](../SKILL.md)直接核验。

## 任务要求文件

`request_artifact` 指向保存的当前原始要求和有效纠正，同时列入 artifacts；所有 artifacts 使用实际文件的绝对路径。评审者直接读取父任务原始要求，核对保存内容是否完整。

```json
{
  "schema_version": 4,
  "task_id": "文档填写实验",
  "task_type": "document",
  "goal": "按用户真实信息填好并保存指定字段",
  "request_artifact": "/实际启动目录/.codex/verification/实际任务/唯一运行/原始要求.md",
  "scope": {
    "allowed_actions": [
      {"operation": "write", "target": "/用户指定位置/目标文档.docx", "request_quote": "填好并保存指定字段"}
    ]
  },
  "criteria": [
    {"id": "C1", "description": "保存后重开，指定字段真实且可编辑", "required": true}
  ],
  "artifacts": [
    "/实际启动目录/.codex/verification/实际任务/唯一运行/原始要求.md",
    "/用户指定位置/目标文档.docx",
    "/实际启动目录/.codex/verification/实际任务/唯一运行/验证报告.json"
  ]
}
```

task_type 为 code / document / computer / research / mixed；至少一项 required=true。运行时将示例路径替换为真实文件路径，缺失工件按缺口处理。

版本比对将上游归档、更新前备份等必要原始输入纳入 artifacts，并按实际结果区分逐字节一致、保留本地差异和局部比较。核对技能安装时，分别保存路径枚举、宿主发现、正文读取和实际执行的对应证据。

coverage、integrity、scope、binding、protocol 为保留 ID；criterion 和 claim 的 ID 互不重复。推荐必要项用 C1、关键主张用 F1，便于分别定位缺口及下一动作。

scope.allowed_actions 记录业务文件写入、删除、命令执行、安装、发送与发布，operation 为 write / delete / execute / install / send / publish。target 是精确目标；write/delete 必须用规范化绝对路径。request_quote 引用原请求中支持该操作的单行文字。评审者依据原话核对授权和操作必要性；纯只读任务可使用空允许列表。验收器自身的状态和报告写入另行处理，业务输出及额外副作用均须计入业务操作。

脚本核对引文是否存在、操作和目标是否匹配。任务要求文件遗漏必要操作时，先核对已有授权，再更新文件并重新评审；需要新业务选择或权限时，只暂停依赖部分。

编辑既有文档时，criteria 须包含原格式与结构保持要求；允许的转换、删栏或局部适配写明既有授权，原件和副本纳入 artifacts。独立评审逐项核对文档内部的实际差异：未经允许的变化反馈 fail，缺少对照证据反馈 unverified。

## 独立评审

父代理提供原始要求、有效纠正、待交付答复和当前工件。评审者只读核对实际结果、来源语义、授权及自身独立身份，返回下列原始 JSON，由父代理原样保存。无法读取实际工件时，将对应项保留为未验证。

```json
{
  "reviewer": {"kind": "independent", "id": "实际独立代理ID"},
  "coverage": {"status": "pass", "reason": "已直接对照原要求和纠正，必要结果没有漏列", "missing_requirements": []},
  "criteria": [
    {"id": "C1", "status": "pass", "reason": "保存后重开和关键字段检查符合原要求", "evidence": ["/实际启动目录/.codex/verification/实际任务/唯一运行/验证报告.json"]}
  ],
  "next_actions": [],
  "integrity": {"status": "pass", "reason": "已核对实际工件和授权范围，本次观察未发现伪证或越权", "evidence": ["/实际启动目录/.codex/verification/实际任务/唯一运行/验证报告.json"]},
  "claims": [
    {
      "id": "F1", "text": "目标文档的指定字段已核验为可编辑",
      "kind": "fact", "basis": "observed", "required": true,
      "reason": "对照实际重开记录；引用只定位记录，语义由评审者核对",
      "sources": [
        {"artifact": "/实际启动目录/.codex/verification/实际任务/唯一运行/验证报告.json", "line": 8, "quote": "\"editable\": true"}
      ]
    }
  ],
  "scope": {
    "status": "pass", "reason": "实际差异和操作记录只涉及获授权的目标",
    "evidence": ["/实际启动目录/.codex/verification/实际任务/唯一运行/验证报告.json"],
    "actions": [{"operation": "write", "target": "/用户指定位置/目标文档.docx"}]
  }
}
```

criteria 必须与任务要求文件中的 ID 一一对应；coverage 单独反馈其中遗漏的原要求，写入 missing_requirements。此列表非空时，即使 coverage.status=pass，整体结果仍为 fail。发现遗漏要求后，补充任务要求文件并重新评审；已启用门禁实验时，还须重新登记。

判据更正按[执行与恢复中的判据更正](execution-and-recovery.md#判据更正)核实。将更正前后的判据、依据与影响记入现有 reason、证据及原计划；required、核验对象、证据门槛或结论范围发生变化时，按同一规则记录和核验，沿用现有 JSON 字段。

正式重新评审时，使用新的独立 run_id 目录，将旧轮输入、判断和报告保留原处，在新记录中核验受影响项。已有独立运行记录的任务，沿用[修复记录约定](execution-and-recovery.md#回修与跨轮恢复)。

## 关键主张与范围核查

claims 至少一项，逐条覆盖最终交付中的关键事实、推断与未知，包含 id、text、kind、basis、required、reason、sources。kind 为 fact / inference / unknown，表示最终交付如何表述；basis 为 observed / inferred / missing / contradicted，表示评审者核对后的依据。required 按必要验收是否依赖这条结论填写。评审者对照最终答复和工件，补查作者清单外的关键主张。

| 情况 | 处理 |
| --- | --- |
| fact + observed 且真实来源支持结论 | 可以作为必要验收依据；仍要核对语义 |
| fact + inferred/contradicted，或 inference + contradicted | fail，并要求修正表述或撤回冲突结论 |
| fact/inference 缺来源、引用不匹配，或必要结论仍是 inference/unknown | partial，补证或暂停依赖该结论的动作 |
| 明确标注的可选 inference，且有可核对依据 | 可保留推断并继续交付 |
| 明确保留的可选 unknown，且没有必要结论依赖它 | 可保留未知并继续交付 |

sources 的每项为已声明工件绝对路径 artifact、1–100000 的整数行号 line、最长1000字的非空单行 quote。引文必须存在于该 UTF-8 文件的指定行。Word/PDF/图片等使用实际提取或渲染核验记录的正文作为定位，原文件同时保留在 artifacts。结果主张引用实际结果记录，示例行号与引文须替换为真实内容。

对结论强度起决定作用的主张，reason 写明实际证据层级：1 作者断言；2 定位到 `file:line` 或上游原文；3 推演出坏情况不可达；4 运行真实代码或命令证明；5 在运行中的目标里复现。第 1 级不足以填写 observed；停在第 2 或第 3 级时，功能可用性或改动生效情况须标明尚未实际运行验证。按结论选择所需证据层级，主结果取值与任务分流保持原规则。本方法借鉴 pstack `blast-radius`（MIT，固定提交 `fe53d9e9`）。

scope.actions 由评审者依据实际差异、工具日志或 trace 列出实质业务操作及副作用。任何 operation/target 不在允许列表中均 fail；scope 和 integrity 的 pass 须有实际核查证据。实际没有这些业务操作时，actions 才可为空。

来源可信度、操作清单完整性和评审独立性由评审者核对；已知并发或外部修改影响结论时，重新核验相关内容。操作示例和不确定性处理见[防编造与范围核查](execution-and-recovery.md)。

## 检查状态与恢复

CLI 的状态按以下顺序确定：必要失败、事实冲突或越界产生 fail；缺证或未核查产生 partial；仅作者自检产生 provisional；提交记录满足检查且标为独立评审时产生 pass。独立身份仍由评审者和父代理核实。

自检报告单独显示“独立评审未完成”。self 且缺少 protocol 下一动作时，脚本补充在新目录进行独立评审的提示，已有恢复动作保留原文。

必要项显式 fail / unverified、coverage 缺口、integrity 或 scope 非 pass，须有下一动作。例如：

```json
[
  {"id": "coverage", "action": "将原要求中的可编辑性补入任务要求文件，再实际重开验证"},
  {"id": "C1", "action": "修复指定字段后保存重开并保留新证据"},
  {"id": "integrity", "action": "核验原始证据与授权；无法继续则保留未完成和恢复条件"}
]
```

脚本按 criteria、claims、integrity、scope 或 protocol 的具体缺口补充提示；声明工件缺失或不是文件时，使用 binding 动作 ID 提示读取实际对象。现场未验证或结论未知时保留对应动作，已有判断和动作保持原文。执行者据此处理仍可推进的必要项；续跑次数用尽时，按实际结果保留未完成项。

### 旧版输入

v2/v3 按可支持字段读取，旧摘要字段被忽略；未声明版本的旧输入因缺少新核查保留 partial 或 fail。
