<!-- @author Pjh -->
# 来源与采用理由

- [Da1sypetals：AGENTS.md](https://github.com/Da1sypetals/AGENTS.md/blob/a475456fe0f99ad40a9f974c5f918d2d4f482546/AGENTS.md)：本技能采用其中的语言要求，使用常用中文、完整词语和动宾结构，保留标识符原名，直接描述当前对象与结果；修改经过留在任务材料中。
- [lennney：STSS](https://github.com/lennney/stop-that-shit/blob/c8d0771f6bfe1cbfa8120fe0c0e9b23540d6a3bd/skills/stss/SKILL.md) 与 [STS](https://github.com/lennney/stop-that-shit/blob/c8d0771f6bfe1cbfa8120fe0c0e9b23540d6a3bd/skills/stop-that-shit/SKILL.md)：STSS 用读者用途逐句判断内容，STS 要求完整履行当前责任并保留必要保障。本技能据此结合章节用途判断内容取舍，保留会改变理解、操作或判断的事实、条件、权限和失败处置，并在删改后核对原目标。
- [Microsoft：写作风格的十项建议](https://learn.microsoft.com/style-guide/top-10-tips-style-voice)：从读者需要完成的事情组织内容，采用直接表达。本技能据此让用途、行为和操作先于实现细节。
- [Google Technical Writing：受众](https://developers.google.com/tech-writing/one/audience)：根据读者已有知识与完成任务所需知识之间的差距决定解释内容。本技能据此区分概览中的作用说明和字段参考中的精确名称。
- [Google Developer Documentation Style Guide：提示与告警](https://developers.google.com/style/notices)：提示应服务当前操作，连续提示可能需要重组正文。本技能据此将告警放到受影响的操作旁，合并重复提醒，并保留真实后果和前置条件。
- [Diátaxis](https://diataxis.fr/)：教程、操作指南、参考与解释承担不同用途。本技能据此按文件各部分的用途组织内容。
- [Michael Nygard：记录架构决定](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)：用简短记录保存单项决定、状态和后果，被替代的记录仍可解释过去。本技能据此保留 ADR 的历史决定，在状态与当前说明中交代变化。
- [Matt Pocock：improve-codebase-architecture](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/improve-codebase-architecture/SKILL.md)：按用户范围或近期变更探索，从新读者的实际阅读摩擦提出具体候选，并尊重已有术语与决策。本技能的集中整理分支据此设计，以位置、读者影响和最小处理方式排序候选；实施沿用本地授权。
- [pstack：technical-writing](https://github.com/cursor/plugins/blob/bb68f2365eceafa0cb2d253112f675acf5f144cc/pstack/skills/technical-writing/SKILL.md)：结合文档用途、明确动作与消除歧义组织表达，保留精确名称，表达变差时保留原文。本技能采用这些取舍，按文体修订，保留条件与含义。
- [pstack：maintain-verification-skill](https://github.com/cursor/plugins/blob/bb68f2365eceafa0cb2d253112f675acf5f144cc/pstack/skills/maintain-verification-skill/SKILL.md)：从导航和源码进入实际核验，区分文档漂移、工具缺口与产品缺陷，只修已证实的范围内问题。本技能采用沿阅读路径核对、复查受影响路径的方法，将验证深度与本次文档用途匹配。
- [Anthropic：doc-coauthoring](https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md)：Reader Testing 让没有作者上下文的新读者只看成稿回答实际问题，发现隐含前提与矛盾。本技能将其作为重要新文档或较大整理缺少读者视角时的可选复查方法。
- [Tencent CloudBase：doc-freshness-review](https://github.com/TencentCloudBase/CloudBase-AI-Toolkit/blob/main/skills/doc-freshness-review/SKILL.md)：将文档声称的文件、命令、生成物与发布入口对应到实际对象，并检查 README 与正文漂移。这为本技能逐项核对现状、直接修复已查明问题的设计提供参考，产品语义未明时保留具体问题。
- [Next.js：update-docs](https://github.com/vercel/next.js/blob/canary/.agents/skills/update-docs/SKILL.md)：从实际代码变化定位相关文档，共享内容修改其源文件。这用于交叉核对范围选择与源文件归属，具体实施仍按目标项目约定。
