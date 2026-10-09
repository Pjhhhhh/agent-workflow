<!-- @author Pjh -->
# 工作验收协议 v3

主结果：`fail` = 必要结果、原要求覆盖、事实表述或操作范围明确失败；`partial` = 必要项未验证、引用缺失、范围未核查或版本不一致；`provisional` = 仅作者自检；`pass` = 以上缺口均无，且为独立评审。新任务只使用 v3 逐项验收，不填写旧五维分数。旧 v2 和未声明 schema_version 的输入仍可读取，但缺少新核查只能得到 partial 或 fail，不能继续得到 pass。

自检报告单独显示“独立评审未完成”；必要项证据缺口为空也不表示整体验收完成。self 且缺少 protocol 下一动作时，脚本补充新目录补审提示；已有恢复动作保留原文。失败与证据缺口仍优先产生 fail / partial，不因 self 降为 provisional。

## 验收契约

`request_artifact` 指向保存的当前原始要求和有效纠正。它必须同时列入 artifacts；所有 artifacts 是实际文件的绝对路径。脚本可绑定这个文件版本，不能验证整理者是否漏录原话，评审者须直接接触父任务原始要求。

```json
{
  "schema_version": 3,
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

task_type 为 code / document / computer / research / mixed；至少一项 required=true。路径是格式示例，运行时用真实文件；缺失工件不得伪造补齐。

版本比对须保留能复现结论的原始输入，例如上游归档与更新前备份，并将必要输入纳入 artifacts。逐字节一致、有意保留的本地差异、仅检查部分文件须分别记录；不要把忽略署名等差异后的比较写成“无差异”。安装工具列出的可见路径只能证明枚举结果，宿主发现技能、读取正文和实际执行分别需要对应证据。

v3 的 criterion/claim ID 不占用 coverage、integrity、scope、binding、protocol；claim ID 也不与 criterion ID 重复，以免不同缺口的下一动作混淆。推荐必要项用 C1、关键主张用 F1。

scope.allowed_actions 记录业务文件写入、删除、命令执行、安装、发送与发布，operation 为 write / delete / execute / install / send / publish。target 是精确目标；write/delete 必须用规范化绝对路径。request_quote 引用原请求中支持该操作的单行文字，评审者同时判断原话是否真的授权以及操作是否必要。纯只读任务可使用空允许列表。验收器自己的状态和报告写入不计入业务操作；不得借此排除业务输出或额外副作用。

允许列表是验收边界，不产生新权限。脚本只能核对引文存在及操作/目标是否匹配，不能从一句话自动推断肯定、否定或隐含授权。契约遗漏必要操作时先核对已有授权、更新契约和重评；需要新业务选择或权限时只暂停依赖部分。

文件级write匹配不证明其中的结构、样式或附加内容获准。编辑既有文档时，criteria须包含原格式与结构保持；允许的转换、删栏或局部适配写明既有授权，原件和副本纳入artifacts。独立评审核对实际差异：未经允许的变化反馈fail，缺对照证据反馈unverified；机器不会从文件名或截图自动判断这些语义。

## 独立评审

下面展示当前 v3 评审的完整字段。父代理提供原始要求和待交付答复，评审者只读返回 JSON，父代理原样保存 judgment.json。SHA256 由评审者实际读取文件计算；无法读到的 artifact 哈希为 null，相关结果为 unverified。哈希占位符不能直接用于实际验收。

```json
{
  "reviewer": {"kind": "independent", "id": "实际独立代理ID"},
  "contract_sha256": "评审时契约的64位SHA256",
  "artifact_hashes": {
    "/实际启动目录/.codex/verification/实际任务/唯一运行/原始要求.md": "评审时文件SHA256",
    "/用户指定位置/目标文档.docx": "评审时文件SHA256",
    "/实际启动目录/.codex/verification/实际任务/唯一运行/验证报告.json": "评审时文件SHA256"
  },
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

criteria 必须与契约 ID 一一对应；coverage 独立反馈**契约外遗漏**，不把遗漏强塞入 criteria。missing_requirements 记录遗漏的原要求，即使 coverage.status=pass 但此列表非空仍整体 fail。发现漏项后修订契约并重评；仅在已启用门禁实验时重新登记，不能为了通过降低要求。

## 关键主张与范围核查

claims 至少一项，逐条覆盖最终交付中的关键事实、推断与未知，包含 id、text、kind、basis、required、reason、sources。kind 为 fact / inference / unknown，表示最终交付如何表述；basis 为 observed / inferred / missing / contradicted，表示评审者核对后的依据。required 表示必要验收是否依赖这条结论，不能为了通过把关键结论改成可选。评审者须对照最终答复和工件查找清单外主张，而不是只读作者提供的清单。

| 情况 | 处理 |
| --- | --- |
| fact + observed 且真实来源支持结论 | 可以作为必要验收依据；仍要核对语义 |
| fact + inferred/contradicted，或 inference + contradicted | fail，并要求修正表述或撤回冲突结论 |
| fact/inference 缺来源、引用不匹配，或必要结论仍是 inference/unknown | partial，补证或暂停依赖该结论的动作 |
| 明确标注的可选 inference，且有可核对依据 | 不因合理推断本身阻断交付 |
| 明确保留的可选 unknown | 可保留未知；没有必要结论依赖它时不阻断交付 |

sources 的每项为已声明工件绝对路径 artifact、1–100000 的整数行号 line、最长1000字的非空单行 quote。引文必须存在于该 UTF-8 文件的指定行。Word/PDF/图片等使用实际提取或渲染核验记录的正文作为定位，原文件同时保留在 artifacts；原请求不能当作结果来源。占位行号与引文必须换成真实记录。

scope.actions 由评审者依据实际差异、工具日志或 trace 列出实质业务操作。任何 operation/target 不在允许列表中均 fail；scope 的 pass 必须有实际核查证据。仅有原请求不能证明结果完成、integrity 或范围核查通过。空 actions 只适用于实际没有这些业务操作的任务，不能省略副作用。

哈希和正文匹配不能证明引用支持结论、来源可信、操作清单完整或评审身份独立。新字段是确定性辅助检查，不是防编造率认证，也不是执行前拦截。完整操作示例和不确定性处理见 [防编造与范围核查](safety.md)。

必要项显式 fail / unverified、coverage 缺口、integrity 或 scope 非 pass，须有下一动作。例如：

```json
[
  {"id": "coverage", "action": "将原要求中的可编辑性补入契约，再实际重开验证"},
  {"id": "C1", "action": "修复指定字段后保存重开并保留新证据"},
  {"id": "integrity", "action": "核验原始证据与授权；无法继续则保留未完成和恢复条件"}
]
```

机器发现证据缺失或版本不一致时补充重评提示；不会执行该动作。下一动作可以描述真实阻碍及恢复条件，但不能把未知写成通过。必要项仍可推进时执行者应修复，有限续跑用尽也不是完成证据。

## 旧格式兼容边界

旧分数计算已移除，结果不再输出 score 或 dimensions 数值。旧输入中的 dimensions 仅作为未使用的额外字段忽略；旧 v2 与未声明版本的记录仍可读取，但须补齐真实 v3 核查才能通过。`score` 命令和 `work-eval-score` 报告文件名保留调用兼容，执行的是当前逐项验收。实际验收遵循目标项目约定：代码核对真实链路，文档重开并对照模板，电脑操作观察终态，研究核对原始来源。
