<!-- @author Pjh -->
# 验收功能入口

`score` 检查任务要求与评审记录，报告具体缺口。按[输入协议](record-checking-protocol.md)准备 schema 4 输入、当前工件和来源正文。

命令中的文件路径、会话和轮次标识需替换为本次实际值。按[技能位置规则](../SKILL.md#区分技能位置与任务位置)确认脚本位置，文件参数与 `--cwd` 使用绝对路径；参数用法见对应命令的 `--help`。

## 检查已提交记录

```sh
python3 /实际技能目录/scripts/work_eval.py score 任务要求文件 评审文件
```

每次运行使用独立目录保存输入与报告。报告写入任务要求文件所在目录的 `work-eval-score.json` 和 `work-eval-score.md`。

| 退出码 | 结果 | 处理动作 |
| --- | --- | --- |
| `0` | `pass` | 核对报告与实际结果，按任务要求交付 |
| `1` | `fail`、`partial` 或 `provisional` | 读取具体缺口和 `next_actions`，处理后重新检查受影响部分 |
| `2` | 输入、读取或报告写入错误 | 按错误详情修正输入、路径或运行目录后重试 |

`contract_path` 指定报告归属。目录中已有 `.work-eval-write.lock`，或原报告属于其他输入时，命令退出 `2` 并保留原报告；使用独立运行目录处理本次输入。

正常退出时，脚本释放本次取得的空锁。进程中断后，核对锁的归属、本次退出码，以及 JSON 和 Markdown 两份报告是否均属于本次运行；遗留锁按当前文件清理权限处理。

## 维护项目内的 Stop 实验

`arm`、`release`、`hook` 用于已获授权的局部实验，须在含 `.agent-workflow-root` 和标准源码目录的完整维护仓库内调用。

### 登记本轮任务

```sh
python3 /实际技能目录/scripts/work_eval.py arm 任务要求文件 --session 实际会话ID --turn 实际轮次ID --cwd 启动目录
```

成功后输出 `armed: true`，写入启动目录的 `.codex/work-eval/实际会话ID/active.json`。核对其中的输入路径、会话和轮次；同轮重新登记时沿用已使用的续跑次数。登记失败时，按错误详情核对输入文件、会话与轮次、启动目录及仓库布局。

### 保留未完成退出

```sh
python3 /实际技能目录/scripts/work_eval.py release --session 实际会话ID --turn 实际轮次ID --cwd 启动目录 --reason external_block --detail 具体阻碍和恢复条件
```

使用已登记的会话和轮次，`--reason` 可选 `user_stop`、`external_block` 或 `hard_budget`，`--detail` 填写原因与恢复条件。成功后输出 `released_unfinished: true`，在 `active.json` 写入 `release`，保留报告和未完成项；失败时按错误详情核对登记状态、轮次与原因。

### 检查 Stop 协议

```sh
python3 /实际技能目录/scripts/work_eval.py hook
```

从标准输入传入 JSON 事件。检查 Stop 时，事件使用 `hook_event_name: "Stop"`，并提供与登记状态匹配的 `session_id`、`turn_id` 和 `cwd`。

Stop 重新检查当前记录并比较报告。存在必要缺口且本轮尚未续跑时，返回 `decision: "block"` 并将 `continuations` 设为 `1`。已续跑一次，或事件中的 `stop_hook_active` 为 `true` 时，返回未完成提示，按提示处理具体缺口。

当前记录与报告一致且状态为 `pass` 时，返回 `{}`。会话或轮次未匹配登记状态、以及项目外的事件也返回 `{}`；结合本轮登记、运行位置和报告状态判断结果。接入宿主时，按专项授权配置事件，并使用实际 Stop 事件核验续跑行为。

### 重放局部协议

从项目根运行：

```sh
python3 scripts/verify_protocol.py
```

核对本次报告的 `cases`、`pass` 和实际命令结果。输入、命令、退出码和输出保存在 `.codex/verification/协议回放-时间/`，操作说明见[维护说明](https://github.com/Pjhhhhh/agent-workflow/blob/main/docs/维护说明.md#重放协议)。

## 恢复同一任务

1. 按[技能的位置与恢复规则](../SKILL.md#区分技能位置与任务位置)和项目约定定位原计划，读取有效要求与授权、最新纠正、当前工件、任务标识、未完成项及证据、已有尝试与下一动作。原任务使用 CLI 时，沿用其 `task_id` 和输入路径。
2. 核对当前工件与证据，补查有变化、已失效或仍待验证的部分。
3. 按本轮有效要求核对目标和范围，确定受影响结果及必要复核。
4. 继续局部 hook 实验时，取得宿主实际 `session` / `turn`，用 `arm` 登记本轮输入。
5. 执行原计划的下一动作，验证结果并更新计划。CLI 新轮记录使用独立目录；存在阻碍时，写明未完成项和恢复条件。

## 按失败维护入口

更新命令、字段和前置条件时，按[维护说明](https://github.com/Pjhhhhh/agent-workflow/blob/main/docs/维护说明.md#按失败维护入口)核验受影响行为并更新本页。
