<!-- @author Pjh -->
# agent-workflow

按任务选择两个独立技能，让 AI 代理完成工作并核对实际结果。

| 技能 | 用途 |
| --- | --- |
| [work-eval](skills/work-eval/SKILL.md) | 组织代码、文档、电脑操作和资料研究任务的执行、核验与恢复 |
| [doc-maintenance](skills/doc-maintenance/SKILL.md) | 处理文档任务，按读者用途编写、核对与整理内容 |

## 开始使用

使用支持 Agent Skills 的客户端，按需安装对应技能。安装器需要 Node.js 22.20+；默认安装到当前项目，在命令末尾加 `-g` 可安装到用户级目录。

安装工作流：

```sh
npx skills add Pjhhhhh/agent-workflow --skill work-eval
```

安装文档编写与处理技能：

```sh
npx skills add Pjhhhhh/agent-workflow --skill doc-maintenance
```

安装后在宿主中调用对应技能。完整目录复制、源码链接和安装确认见[安装与更新](docs/安装与更新.md)；文档任务的具体入口见[安装 doc-maintenance](docs/安装与更新.md#安装-doc-maintenance)。

## 文档任务

文档任务使用 `doc-maintenance`，并按宿主或项目规则读取用户已配置的文档规范；规范不随技能安装。局部编写与处理核对目标内容，集中整理再检查跨页阅读路径。

## 按问题查阅

| 要做什么 | 阅读入口 |
| --- | --- |
| 安装、更新、确认生效或退出 | [安装与更新](docs/安装与更新.md) |
| 了解任务执行、验证与恢复 | [工作流程](docs/工作流程.md) |
| 查项目说明、工具、验证与研究材料 | [文档导航](docs/README.md) |
|                  |                        |

## 许可

项目自有内容采用[MIT许可](LICENSE)。图集的第三方和内嵌字体声明见[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。私人计划、业务材料、会话、配置和浏览器日志不随仓库提交。
