<!-- @author Pjh -->
# 第三方许可

`docs/diagrams/*.html` 使用 Archify 2.17 生成并包含其交互查看器。以下保留上游 MIT 声明；项目内容使用根目录 MIT 许可。

```text
MIT License

Copyright (c) 2026 tt-a1i (Archify)
Copyright (c) 2025 Cocoon AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 图中内嵌字体

四张流程图包含 JetBrains Mono 字体及其 SIL Open Font License 1.1 声明，声明随 HTML 保留；分发或重新生成时不要剥离其中的许可文本。

## pstack 参考来源

本仓库不分发 pstack 的技能正文。可选接入说明列出 `create-verification-skill`、`maintain-verification-skill`、`benchmark-checklist`、`blast-radius`、`correct` 的调用条件与权限边界；克隆本仓库不会取得这些技能，使用者按当前授权另行安装或适配。

[可选接入说明](skills/work-eval/references/optional-integrations.md#项目验证性能结论与变更影响技能pstack-移植) 只提供出处和使用条件；`skills/work-eval/references/rubric.md` 的关键主张证据强度阶梯借鉴 [cursor/plugins 的 pstack 插件](https://github.com/cursor/plugins/tree/fe53d9e9093dbb9ae298563b1a9d702dd6e2ca08/pstack) 中 [`blast-radius`](https://github.com/cursor/plugins/blob/fe53d9e9093dbb9ae298563b1a9d702dd6e2ca08/pstack/skills/blast-radius/SKILL.md) 的分级思路，该段为中文自写表述。来源作者为 Lauren Tan／poteto，Copyright (c) 2026 Lauren Tan，MIT；锚定提交为 `fe53d9e9093dbb9ae298563b1a9d702dd6e2ca08`，manifest 版本 0.15.21。上游许可原文见同一提交的 [pstack/LICENSE](https://github.com/cursor/plugins/blob/fe53d9e9093dbb9ae298563b1a9d702dd6e2ca08/pstack/LICENSE)。
