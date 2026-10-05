"""生成可重跑的合成自检和版本失效示例，不冒充独立业务验收。@author Pjh"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def save(path, value):
    """保留精确输入和命令结果供读者核对。@author Pjh"""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    """在独立目录执行真实评分CLI，只接受约定的未完成状态。@author Pjh"""
    source = Path(__file__).resolve().parents[1]
    run = Path.cwd() / '.codex' / 'verification' / ('demo-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    run.mkdir(parents=True)
    results = []
    for name, expected in [('self', 'provisional'), ('changed', 'partial')]:
        folder = run / name
        folder.mkdir()
        request, artifact = folder / 'request.txt', folder / 'artifact.txt'
        request.write_text('合成要求：写入演示文件。\n', encoding='utf-8')
        artifact.write_text('这是合成演示文件，不是业务结果。\n', encoding='utf-8')
        cp, jp = folder / 'contract.json', folder / 'judgment.json'
        proof = [str(artifact)]
        action = {'operation': 'write', 'target': str(artifact)}
        save(cp, {'schema_version': 3, 'task_id': 'demo-' + name, 'task_type': 'document',
                  'goal': '验证合成协议状态', 'request_artifact': str(request),
                  'scope': {'allowed_actions': [dict(action, request_quote='写入演示文件')]},
                  'criteria': [{'id': 'C1', 'description': '合成文件存在且内容符合示例', 'required': True}],
                  'artifacts': [str(request), str(artifact)]})
        save(jp, {'reviewer': {'kind': 'self', 'id': 'synthetic-example-not-a-reviewer'},
                  'contract_sha256': digest(cp), 'artifact_hashes': {str(p): digest(p) for p in [request, artifact]},
                  'coverage': {'status': 'pass', 'reason': '仅为合成输入', 'missing_requirements': []},
                  'criteria': [{'id': 'C1', 'status': 'pass', 'reason': '合成输入已生成', 'evidence': proof}],
                  'integrity': {'status': 'pass', 'reason': '合成数据未声称真实业务通过', 'evidence': proof},
                  'scope': {'status': 'pass', 'reason': '仅写示例文件', 'evidence': proof, 'actions': [action]},
                  'claims': [{'id': 'F1', 'text': '这是合成演示文件', 'kind': 'fact', 'basis': 'observed',
                              'required': True, 'reason': '读取示例正文',
                              'sources': [{'artifact': str(artifact), 'line': 1, 'quote': '这是合成演示文件'}]}],
                  'next_actions': []})
        if name == 'changed':
            artifact.write_text(artifact.read_text(encoding='utf-8') + '评审后增加的内容。\n', encoding='utf-8')
        command = [sys.executable, str(source / 'skills/work-eval/scripts/work_eval.py'), 'score', str(cp), str(jp)]
        result = subprocess.run(command, capture_output=True, text=True)
        save(folder / 'invocation.json', {'command': command, 'exit_code': result.returncode,
                                         'stdout': result.stdout, 'stderr': result.stderr})
        report = json.loads(result.stdout) if result.stdout.strip() else {}
        results.append({'case': name, 'status': report.get('status'), 'exit_code': result.returncode,
                        'expected': expected, 'ok': result.returncode == 1 and report.get('status') == expected})
    save(run / 'summary.json', {'synthetic': True, 'results': results})
    print(json.dumps({'output': str(run), 'results': results}, ensure_ascii=False))
    return 0 if all(r['ok'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
