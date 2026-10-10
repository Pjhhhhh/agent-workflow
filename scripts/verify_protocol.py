"""用真实命令和hook输入回放评分边界，合成案例仅证明协议行为。@author Pjh"""

import copy
import hashlib
import json
import os
import subprocess
import sys
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Union

FixtureEdit = Optional[Callable[[dict, dict, Path], None]]

PROJECT = Path(__file__).resolve().parents[1]
ROOT = Path.cwd() / '.codex' / 'verification'
ROOT.mkdir(parents=True, exist_ok=True)
SCRIPT = PROJECT / 'skills' / 'work-eval' / 'scripts' / 'work_eval.py'
RUN = ROOT / ('协议回放-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
RUN.mkdir()
RESULTS = []
START_HASH = hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
START_REPLAY_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def save(path: Path, value: dict) -> None:
    """保留输入与输出，便于独立重放。@author Pjh"""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh_contract(c: dict, j: dict, artifact: Path) -> None:
    """结构案例同步契约版本，避免被无关哈希差异代替目标失败。@author Pjh"""
    cp = artifact.parent / 'contract.json'
    save(cp, c)
    j['contract_sha256'] = sha(cp)


def request_alias(c: dict, j: dict, artifact: Path, mode: str, channel: str = 'criteria') -> None:
    """复现同一原请求换路径后的证据冒用，链接留在本例目录供重放。@author Pjh"""
    request = Path(c['request_artifact'])
    if mode == 'alias':
        alias = str(request.parent) + '/./' + request.name
    else:
        path = request.parent / ('请求' + mode + '.txt')
        if mode == 'symlink':
            path.symlink_to(request)
        else:
            os.link(request, path)
        alias = str(path)
    c['artifacts'].append(alias)
    j['artifact_hashes'][alias] = sha(Path(alias))
    if channel == 'claims':
        j['claims'][0]['sources'] = [{'artifact': alias, 'line': 1, 'quote': '写入合成协议工件'}]
    elif channel == 'criteria':
        j['criteria'][0]['evidence'] = [alias]
    else:
        j[channel]['evidence'] = [alias]
    refresh_contract(c, j, artifact)


def call(label: str, args: list[Union[str, Path]], stdin: Optional[str] = None) -> tuple:
    """只执行本地评分器，不执行工件里声明的任何命令。@author Pjh"""
    command = [sys.executable, str(SCRIPT)] + [str(x) for x in args]
    result = subprocess.run(command, input=stdin, capture_output=True, text=True)
    save(RUN / (label + '.json'), {'command': command, 'stdin': stdin,
         'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    if args[0] != 'score' and result.returncode != 0:
        raise RuntimeError(label + ': 命令失败，见本例日志')
    value = json.loads(result.stdout) if result.stdout.strip() else {}
    return result.returncode, value


def check(label: str, condition: bool) -> None:
    RESULTS.append({'case': label, 'pass': bool(condition)})


def scenario(name: str, edit: FixtureEdit = None) -> tuple:
    """每例单独的契约与工件，不覆盖前次回放。@author Pjh"""
    folder = RUN / name
    folder.mkdir()
    artifact = folder / '实际工件.txt'
    artifact.write_text('本例合成协议工件，不是业务验收。\n', encoding='utf-8')
    request = folder / '原始要求.txt'
    request.write_text('本例要求：写入合成协议工件并核验内容。\n', encoding='utf-8')
    contract = {'schema_version': 3, 'task_id': name, 'task_type': 'mixed', 'goal': '合成协议回放',
                'criteria': [{'id': 'C1', 'description': '本例必要项', 'required': True}],
                'scope': {'allowed_actions': [{'operation': 'write', 'target': str(artifact),
                          'request_quote': '写入合成协议工件并核验内容'}]},
                'request_artifact': str(request), 'artifacts': [str(artifact), str(request)]}
    cp, jp = folder / 'contract.json', folder / 'judgment.json'
    save(cp, contract)
    proof = [str(artifact)]
    judgment = {'reviewer': {'kind': 'independent', 'id': 'synthetic-protocol-fixture'},
                'contract_sha256': sha(cp), 'artifact_hashes': {str(artifact): sha(artifact), str(request): sha(request)},
                'coverage': {'status': 'pass', 'reason': '合成原请求核对', 'missing_requirements': []},
                'next_actions': [],
                'criteria': [{'id': 'C1', 'status': 'pass', 'reason': '协议fixture', 'evidence': proof}],
                'integrity': {'status': 'pass', 'reason': '合成协议fixture', 'evidence': proof},
                'claims': [{'id': 'F1', 'text': '工件说明本例是合成协议案例', 'kind': 'fact',
                            'basis': 'observed', 'required': True, 'reason': '合成正文片段可核对',
                            'sources': [{'artifact': str(artifact), 'line': 1, 'quote': '本例合成协议工件'}]}],
                'scope': {'status': 'pass', 'reason': '合成操作与允许目标一致', 'evidence': proof,
                          'actions': [{'operation': 'write', 'target': str(artifact)}]}}
    if edit:
        edit(contract, judgment, artifact)
    if name not in {'失败无下一动作', '遗漏无下一动作'} and 'coverage' in judgment:
        for item in judgment['criteria']:
            if item.get('status') in {'fail', 'unverified'}:
                judgment['next_actions'].append({'id': item['id'], 'action': '修复本例对应工件后重验'})
        if judgment['coverage'].get('status') != 'pass' or judgment['coverage'].get('missing_requirements'):
            judgment['next_actions'].append({'id': 'coverage', 'action': '核对原要求并修订契约后重评'})
    save(cp, contract)
    save(jp, judgment)
    return cp, jp, artifact


def score_case(name: str, edit: FixtureEdit, code: int, status: Optional[str] = None,
               expected_actions: Optional[set[str]] = None) -> tuple:
    cp, jp, artifact = scenario(name, edit)
    rc, report = call(name, ['score', cp, jp])
    check(name, rc == code and (status is None or report.get('status') == status))
    if expected_actions is not None:
        actions = report.get('next_actions', [])
        original = json.loads(jp.read_text(encoding='utf-8'))['next_actions']
        check(name + '-下一动作准确且保留原判断', {x['id'] for x in actions} == expected_actions
              and all(x in actions for x in original) and len(actions) == len(expected_actions))
    return cp, jp, artifact, report


success = score_case('成功', None, 0, 'pass', set())
failure = score_case('必要失败仍满分', lambda c, j, a: (j.update(dimensions={'scope': {'rating': 5}}), j['criteria'][0].update(status='fail')), 1, 'fail', {'C1'})
check('旧分数不再输出且不能放行失败', 'score' not in failure[3] and 'dimensions' not in failure[3] and failure[3].get('status') == 'fail')
score_case('未验证', lambda c, j, a: j['criteria'][0].update(status='unverified', reason='现场必要项尚未验证'), 1, 'partial', {'C1'})
score_case('必要项无证据', lambda c, j, a: j['criteria'][0].update(evidence=[]), 1, 'partial', {'C1'})
score_case('遗漏验收', lambda c, j, a: j.update(criteria=[]), 2)
score_case('重复验收', lambda c, j, a: j['criteria'].append(copy.deepcopy(j['criteria'][0])), 2)
score_case('忽略旧布尔评分', lambda c, j, a: j.update(dimensions={'scope': {'rating': True}}), 0, 'pass')
score_case('非有限分数', lambda c, j, a: j.update(dimensions={'scope': {'rating': float('nan')}}), 2)
score_case('忽略旧畸形维度', lambda c, j, a: j.update(dimensions='obsolete'), 0, 'pass')
score_case('空理由', lambda c, j, a: j['criteria'][0].update(reason=''), 2)
self_review = score_case('自评分', lambda c, j, a: j['reviewer'].update(kind='self'), 1, 'provisional', {'protocol'})
self_markdown = (self_review[0].parent / 'work-eval-score.md').read_text(encoding='utf-8')
check('自检报告明确独立评审未完成', '独立评审未完成' in self_markdown and '必要项证据缺口' in self_markdown)
check('自检自动提示补审', any(x['id'] == 'protocol' and '独立评审' in x['action'] for x in self_review[3]['next_actions']))
self_failure = score_case('自检失败优先', lambda c, j, a: (j['reviewer'].update(kind='self'), j['criteria'][0].update(status='fail')), 1, 'fail', {'C1', 'protocol'})
self_unknown = score_case('自检未知优先', lambda c, j, a: (j['reviewer'].update(kind='self'), j['criteria'][0].update(status='unverified')), 1, 'partial', {'C1', 'protocol'})
check('自检失败未知也显示评审缺口', all('独立评审未完成' in (x[0].parent / 'work-eval-score.md').read_text(encoding='utf-8') for x in (self_failure, self_unknown)))
self_recovery = score_case('自检保留恢复动作', lambda c, j, a: (j['reviewer'].update(kind='self'), j['next_actions'].append({'id': 'protocol', 'action': '容量恢复后补独立评审'})), 1, 'provisional')
check('不重复改写已有恢复动作', [x for x in self_recovery[3]['next_actions'] if x['id'] == 'protocol'] == [{'id': 'protocol', 'action': '容量恢复后补独立评审'}])
check('独立通过没有自检提示', '独立评审未完成' not in (success[0].parent / 'work-eval-score.md').read_text(encoding='utf-8'))
score_case('契约同ID已变', lambda c, j, a: c.update(goal='修改后的目标'), 1, 'partial', {'binding'})
score_case('工件已变', lambda c, j, a: a.write_text('变化的版本', encoding='utf-8'), 1, 'partial', {'F1', 'binding'})

def missing(c: dict, j: dict, artifact: Path) -> None:
    """声明缺失文件，不删除任何现有文件。@author Pjh"""
    path = str(artifact.parent / '未生成工件.txt')
    c['artifacts'].append(path)
    save(artifact.parent / 'contract.json', c)
    j['contract_sha256'] = sha(artifact.parent / 'contract.json')
    j['artifact_hashes'][path] = None

score_case('缺失文件', missing, 1, 'partial', {'binding'})
score_case('声明目录不是文件', lambda c, j, a: (c['artifacts'].append(str(a.parent)),
           j['artifact_hashes'].update({str(a.parent): None}), refresh_contract(c, j, a)), 1, 'partial', {'binding'})
score_case('现场未验证兼版本失效', lambda c, j, a: (j['criteria'][0].update(status='unverified'),
           j['artifact_hashes'].update({str(a): '0' * 64})), 1, 'partial', {'C1', 'binding'})
score_case('必要失败兼版本失效', lambda c, j, a: (j['criteria'][0].update(status='fail'),
           j['artifact_hashes'].update({str(a): '0' * 64})), 1, 'fail', {'C1', 'binding'})
score_case('保留已有binding动作', lambda c, j, a: (j['artifact_hashes'].update({str(a): '0' * 64}),
           j['next_actions'].append({'id': 'binding', 'action': '按原判断核对失效工件后重评'})), 1, 'partial', {'binding'})

def optional(c: dict, j: dict, artifact: Path) -> None:
    c['criteria'].append({'id': 'O1', 'description': '可选项', 'required': False})
    save(artifact.parent / 'contract.json', c)
    j['contract_sha256'] = sha(artifact.parent / 'contract.json')
    j['criteria'].append({'id': 'O1', 'status': 'pass', 'reason': '缺证据', 'evidence': []})

opt = score_case('可选项无证据', optional, 0, 'pass', {'O1'})
check('可选项不伪标通过', opt[3]['criteria'][1]['status'] == 'unverified')

score_case('低分必要通过', lambda c, j, a: j.update(dimensions={'scope': {'rating': 1, 'evidence': []}}), 0, 'pass')
current = score_case('默认无旧评分', None, 0, 'pass')
check('当前输出无旧评分字段', 'score' not in current[3] and 'dimensions' not in current[3])
rendered = (current[0].parent / 'work-eval-score.md').read_text(encoding='utf-8')
check('可读报告逐项展示', '| C1 | pass |' in rendered and '维度' not in rendered and '可选描述分数' not in rendered)
score_case('原请求未核对', lambda c, j, a: j['coverage'].update(status='unverified'), 1, 'partial', {'coverage'})
score_case('原要求遗漏', lambda c, j, a: j['coverage'].update(missing_requirements=['要求还包括可编辑性']), 1, 'fail')
score_case('失败无下一动作', lambda c, j, a: j['criteria'][0].update(status='fail'), 2)
score_case('遗漏无下一动作', lambda c, j, a: j['coverage'].update(missing_requirements=['本例漏项']), 2)
score_case('原请求已变', lambda c, j, a: Path(c['request_artifact']).write_text('新原要求', encoding='utf-8'), 1, 'partial', {'scope', 'binding'})
score_case('缺覆盖检查', lambda c, j, a: j.pop('coverage'), 2)
score_case('真实性失败无动作', lambda c, j, a: j['integrity'].update(status='fail'), 2)
score_case('真实性失败有动作', lambda c, j, a: (j['integrity'].update(status='fail'), j['next_actions'].append({'id': 'integrity', 'action': '核验原始证据，原授权内修复后重评'})), 1, 'fail')
score_case('真实性未验证无动作', lambda c, j, a: j['integrity'].update(status='unverified'), 2)
score_case('真实性未验证保留动作', lambda c, j, a: (j['integrity'].update(status='unverified'),
           j['next_actions'].append({'id': 'integrity', 'action': '补取实际真实性核查证据'})), 1, 'partial', {'integrity'})

# 先冻结这些黑盒失败输入，再修改验收器，避免只检查实现自己选择的成功路径。
score_case('原要求冒充完成证据', lambda c, j, a: j['criteria'][0].update(evidence=[c['request_artifact']]), 1, 'partial', {'C1'})
score_case('真实性通过无核查证据', lambda c, j, a: j['integrity'].update(evidence=[]), 1, 'partial', {'integrity'})
score_case('推断冒充事实', lambda c, j, a: j['claims'][0].update(basis='inferred'), 1, 'fail')
score_case('反证仍称事实', lambda c, j, a: j['claims'][0].update(basis='contradicted'), 1, 'fail')
score_case('未知仍称事实', lambda c, j, a: j['claims'][0].update(basis='missing', sources=[]), 1, 'partial', {'F1'})
score_case('事实缺来源', lambda c, j, a: j['claims'][0].update(sources=[]), 1, 'partial', {'F1'})
score_case('伪造引用正文', lambda c, j, a: j['claims'][0]['sources'][0].update(quote='日志中并不存在的全系统通过'), 1, 'partial', {'F1'})
score_case('引用行号错误', lambda c, j, a: j['claims'][0]['sources'][0].update(line=2), 1, 'partial', {'F1'})
score_case('引用行号为布尔值', lambda c, j, a: j['claims'][0]['sources'][0].update(line=True), 2)
score_case('空引用片段', lambda c, j, a: j['claims'][0]['sources'][0].update(quote=''), 2)
score_case('请求冒充事实来源', lambda c, j, a: j['claims'][0]['sources'][0].update(artifact=c['request_artifact'], quote='写入合成协议工件'), 1, 'partial', {'F1'})
binary = score_case('引用非UTF8正文', lambda c, j, a: (a.write_bytes(b'\xff\xfe'), j['artifact_hashes'].update({str(a): sha(a)})), 1, 'partial', {'F1'})
check('非UTF8仅因正文无法核查', any(x.startswith('F1:') for x in binary[3].get('unverified', [])) and not any('工件已不同' in x for x in binary[3].get('unverified', [])))
score_case('主张未登记', lambda c, j, a: j.pop('claims'), 2)
score_case('主张清单为空', lambda c, j, a: j.update(claims=[]), 2)
score_case('主张ID重复', lambda c, j, a: j['claims'].append(copy.deepcopy(j['claims'][0])), 2)
score_case('主张分类无效', lambda c, j, a: j['claims'][0].update(kind='certified'), 2)
score_case('必要标记不是布尔值', lambda c, j, a: j['claims'][0].update(required=1), 2)
score_case('必要结论仍未知', lambda c, j, a: j['claims'][0].update(kind='unknown', basis='missing', sources=[]), 1, 'partial', {'F1'})
score_case('保留可选未知', lambda c, j, a: j['claims'][0].update(kind='unknown', basis='missing', required=False, sources=[]), 0, 'pass', set())
score_case('注明可选推断', lambda c, j, a: j['claims'][0].update(kind='inference', basis='inferred', required=False), 0, 'pass')
score_case('未授权文件修改', lambda c, j, a: j['scope']['actions'].append({'operation': 'write', 'target': str(a.parent / '旁路文件.txt')}), 1, 'fail')
score_case('未授权安装', lambda c, j, a: j['scope']['actions'].append({'operation': 'install', 'target': '额外软件'}), 1, 'fail')
score_case('未授权发布', lambda c, j, a: j['scope']['actions'].append({'operation': 'publish', 'target': '外部站点'}), 1, 'fail')
score_case('范围核查无证据', lambda c, j, a: j['scope'].update(evidence=[]), 1, 'partial', {'scope'})
score_case('请求冒充范围核查证据', lambda c, j, a: j['scope'].update(evidence=[c['request_artifact']]), 1, 'partial', {'scope'})
score_case('范围未验证保留动作', lambda c, j, a: (j['scope'].update(status='unverified'),
           j['next_actions'].append({'id': 'scope', 'action': '补取完整实际操作记录'})), 1, 'partial', {'scope'})
score_case('允许操作缺失', lambda c, j, a: c.pop('scope'), 2)
score_case('实际操作缺失', lambda c, j, a: j['scope'].pop('actions'), 2)
score_case('实际操作畸形', lambda c, j, a: j['scope']['actions'].append('write'), 2)
authorization = score_case('授权引文不存在', lambda c, j, a: (c['scope']['allowed_actions'][0].update(request_quote='顺便安装软件并发布'), refresh_contract(c, j, a)), 1, 'partial', {'scope'})
check('授权引文缺失原因准确', any('授权引文' in x for x in authorization[3].get('unverified', [])))
legacy = score_case('旧协议不能绕过新核查', lambda c, j, a: (c.pop('schema_version'), c.pop('scope'), j.pop('claims'), j.pop('scope'), refresh_contract(c, j, a)), 1, 'partial', {'protocol'})
check('旧格式缺新核查原因准确', any('旧协议' in x for x in legacy[3].get('unverified', [])))
for mode in ['alias', 'symlink', 'hardlink']:
    score_case('请求同文件冒用-' + mode, lambda c, j, a, mode=mode: request_alias(c, j, a, mode), 1, 'partial', {'C1'})
for channel in ['claims', 'integrity', 'scope']:
    score_case('请求链接冒用-' + channel, lambda c, j, a, channel=channel: request_alias(c, j, a, 'symlink', channel), 1, 'partial', {'F1' if channel == 'claims' else channel})
for identifier in ['scope', 'integrity', 'binding', 'C1']:
    score_case('主张ID与动作冲突-' + identifier, lambda c, j, a, identifier=identifier: j['claims'][0].update(id=identifier), 2)
score_case('验收ID与动作冲突', lambda c, j, a: (c['criteria'][0].update(id='scope'), j['criteria'][0].update(id='scope'), refresh_contract(c, j, a)), 2)

cwd = RUN / '独立会话'
cwd.mkdir()
event = {'hook_event_name': 'Stop', 'session_id': 'protocol-test', 'turn_id': 'turn-1', 'cwd': str(cwd)}
cp, jp, artifact, report = success
call('登记成功', ['arm', cp, '--session', event['session_id'], '--turn', event['turn_id'], '--cwd', cwd])
check('成功Stop放行', call('成功Stop', ['hook'], json.dumps(event))[1] == {})
tamper = cp.parent / 'work-eval-score.json'
changed = json.loads(tamper.read_text(encoding='utf-8'))
changed['status'] = 'forged'
save(tamper, changed)
check('篡改评分被拦', call('篡改评分Stop', ['hook'], json.dumps(event))[1].get('decision') == 'block')
call('同轮重新登记', ['arm', cp, '--session', event['session_id'], '--turn', event['turn_id'], '--cwd', cwd])
check('重登记不重置次数', 'decision' not in call('重登记后Stop', ['hook'], json.dumps(event))[1])
for field, value in [('session_id', 'other-session'), ('turn_id', 'other-turn')]:
    different = dict(event, **{field: value})
    check('隔离-' + field, call('隔离-' + field, ['hook'], json.dumps(different))[1] == {})
no_score, _, _ = scenario('尚无评分')
event['turn_id'] = 'turn-2'
call('登记无评分', ['arm', no_score, '--session', event['session_id'], '--turn', event['turn_id'], '--cwd', cwd])
check('缺评分首次续跑', call('无评分首次Stop', ['hook'], json.dumps(event))[1].get('decision') == 'block')
check('缺评分二次不死循环', 'decision' not in call('无评分二次Stop', ['hook'], json.dumps(event))[1])
call('未完成退出', ['release', '--session', event['session_id'], '--turn', event['turn_id'], '--cwd', cwd,
                  '--reason', 'external_block', '--detail', '本例模拟环境缺失'])
check('退出不伪称通过', '未完成退出' in call('退出Stop', ['hook'], json.dumps(event))[1].get('systemMessage', ''))
rc, result = call('非对象hook', ['hook'], '[]')
check('非对象hook留警告', rc == 0 and '未确认通过' in result.get('systemMessage', ''))
rc, result = call('坏JSONhook', ['hook'], '{')
check('坏JSONhook留警告', rc == 0 and '未确认通过' in result.get('systemMessage', ''))
prompt = dict(event, hook_event_name='UserPromptSubmit')
check('退出后Prompt不注入', call('退出后Prompt', ['hook'], json.dumps(prompt))[1] == {})
call('恢复实验登记', ['arm', no_score, '--session', event['session_id'], '--turn', event['turn_id'], '--cwd', cwd])
check('Prompt注入真实轮次', 'turn-2' in call('Prompt触发', ['hook'], json.dumps(prompt))[1]['hookSpecificOutput']['additionalContext'])
check('新轮无重登记不注入', call('新轮Prompt', ['hook'], json.dumps(dict(prompt, turn_id='turn-3')))[1] == {})
foreign = dict(event, cwd=str(Path('/tmp')), hook_event_name='UserPromptSubmit')
check('项目外Prompt无注入', call('项目外Prompt', ['hook'], json.dumps(foreign))[1] == {})
foreign['hook_event_name'] = 'Stop'
check('项目外Stop无拦截', call('项目外Stop', ['hook'], json.dumps(foreign))[1] == {})

# 用历史反馈里的三个缺口验证闭环；这些状态都是合成输入，不运行真实业务。
cp, jp, artifact = scenario('历史早停闭环')
c, j = json.loads(cp.read_text(encoding='utf-8')), json.loads(jp.read_text(encoding='utf-8'))
request = Path(c['request_artifact'])
request.write_text('本例要求：写入合成协议工件并核验内容。\n'
                   'R006、视觉第2页、视觉第3页是三个必要项，全部通过才完成；不执行真实业务。\n', encoding='utf-8')
c['criteria'] = [{'id': identifier, 'description': description, 'required': True} for identifier, description in
                 [('R006', '合成R006终态'), ('V002', '合成视觉第2页终态')]]
j['criteria'] = [{'id': item['id'], 'status': 'unverified', 'reason': '合成未识别状态，仍需回修',
                  'evidence': [str(artifact)]} for item in c['criteria']]
j['coverage'].update(status='fail', reason='原要求中的视觉第3页漏列', missing_requirements=['视觉第3页'])
j['next_actions'] = [{'id': 'R006', 'action': '定位合成R006未识别原因并验证'},
                     {'id': 'V002', 'action': '补核合成视觉第2页'},
                     {'id': 'coverage', 'action': '补回原要求中的视觉第3页并验收'}]
save(cp, c)
j['contract_sha256'] = sha(cp)
j['artifact_hashes'] = {path: sha(Path(path)) for path in c['artifacts']}
save(jp, j)
save(cp.parent / 'contract-漏列时.json', c)
artifact_initial = artifact.read_text(encoding='utf-8')
(cp.parent / '工件-初始.txt').write_text(artifact_initial, encoding='utf-8')
rc, initial = call('早停-漏列与未识别', ['score', cp, jp])
check('早停-满分仍拒绝三个缺口', rc == 1 and initial.get('status') == 'fail'
      and 'score' not in initial and initial['coverage']['missing_requirements'] == ['视觉第3页']
      and {'R006', 'V002', 'coverage'} <= {x['id'] for x in initial['next_actions']})

c['criteria'].append({'id': 'V003', 'description': '合成视觉第3页终态', 'required': True})
save(cp, c)
rc, _ = call('早停-补要求但沿用旧评审', ['score', cp, jp])
rejected_log = json.loads((RUN / '早停-补要求但沿用旧评审.json').read_text(encoding='utf-8'))
rejected = json.loads(rejected_log['stderr'])
check('早停-新增必要项须重评', rc == 2 and '评审遗漏、重复或新增了验收项' in rejected.get('detail', ''))
j['contract_sha256'] = sha(cp)
j['criteria'].append({'id': 'V003', 'status': 'unverified', 'reason': '合成未识别状态，仍需回修',
                      'evidence': [str(artifact)]})
j['coverage'].update(status='pass', reason='已核对合成原要求的三个必要项', missing_requirements=[])
j['next_actions'] = [x for x in j['next_actions'] if x['id'] != 'coverage']
j['next_actions'].append({'id': 'V003', 'action': '补核合成视觉第3页'})
pending = cp.parent / 'judgment-要求补齐.json'
save(pending, j)
rc, pending_report = call('早停-三个必要项待回修', ['score', cp, pending])
check('早停-缺口逐项保留', rc == 1 and pending_report.get('status') == 'partial'
      and {'R006', 'V002', 'V003'} <= {x['id'] for x in pending_report['next_actions']}
      and all(any(identifier + ':' in entry for entry in pending_report['unverified'])
              for identifier in ['R006', 'V002', 'V003']))

loop_cwd = RUN / '历史早停会话'
loop_cwd.mkdir()
loop = {'hook_event_name': 'Stop', 'session_id': 'closed-loop', 'turn_id': 'before-resume', 'cwd': str(loop_cwd)}
call('早停-登记第一轮', ['arm', cp, '--session', loop['session_id'], '--turn', loop['turn_id'], '--cwd', loop_cwd])
check('早停-未完成请求继续', call('早停-首次Stop', ['hook'], json.dumps(loop))[1].get('decision') == 'block')
warning = call('早停-第二次Stop', ['hook'], json.dumps(loop))[1]
check('早停-续跑上限不等于完成', 'decision' not in warning and '不能声称完成' in warning.get('systemMessage', ''))
loop['turn_id'] = 'after-resume'
check('早停-新轮不猜旧任务', call('早停-新轮未登记Stop', ['hook'], json.dumps(loop))[1] == {})
call('早停-明确恢复原任务', ['arm', cp, '--session', loop['session_id'], '--turn', loop['turn_id'], '--cwd', loop_cwd])
state = json.loads((loop_cwd / '.codex/work-eval/closed-loop/active.json').read_text(encoding='utf-8'))
save(cp.parent / '恢复登记快照.json', state)
check('早停-恢复关联同契约', state['contract'] == str(cp.resolve()) and state['contract_sha256'] == sha(cp)
      and state['turn_id'] == 'after-resume' and state['continuations'] == 0)
check('早停-恢复后旧缺口仍拦', call('早停-恢复Stop', ['hook'], json.dumps(loop))[1].get('decision') == 'block')

artifact.write_text(artifact_initial + '模拟回修：R006=pass，V002和V003仍未验证。\n', encoding='utf-8')
(cp.parent / '工件-部分回修.txt').write_bytes(artifact.read_bytes())
rc, stale = call('早停-回修工件但旧评审', ['score', cp, pending])
check('早停-回修工件须重评', rc == 1 and stale.get('status') == 'partial'
      and '工件已不同于评审者检查的版本' in stale.get('unverified', []))
j['artifact_hashes'][str(artifact)] = sha(artifact)
j['criteria'][0].update(status='pass', reason='仅模拟R006终态已验证')
j['next_actions'] = [x for x in j['next_actions'] if x['id'] != 'R006']
partial_judgment = cp.parent / 'judgment-部分回修.json'
save(partial_judgment, j)
rc, partial_report = call('早停-只修一项', ['score', cp, partial_judgment])
check('早停-局部修复不能结案', rc == 1 and partial_report.get('status') == 'partial'
      and partial_report['criteria'][0]['status'] == 'pass'
      and {'V002', 'V003'} <= {x['id'] for x in partial_report['next_actions']}
      and 'R006' not in {x['id'] for x in partial_report['next_actions']}
      and not any(entry.startswith('R006:') for entry in partial_report['unverified']))

artifact.write_text(artifact_initial + '模拟回修：R006、V002、V003均为pass；不代表真实业务已修复。\n', encoding='utf-8')
(cp.parent / '工件-全部回修.txt').write_bytes(artifact.read_bytes())
j['artifact_hashes'][str(artifact)] = sha(artifact)
for item in j['criteria']:
    item.update(status='pass', reason='合成终态已核验，不代表真实业务')
j['next_actions'] = []
final_judgment = cp.parent / 'judgment-全部回修.json'
save(final_judgment, j)
rc, final_report = call('早停-全部回修后重评', ['score', cp, final_judgment])
check('早停-全部必要项满足才通过', rc == 0 and final_report.get('status') == 'pass'
      and all(x['status'] == 'pass' for x in final_report['criteria'])
      and not final_report['required_failures'] and not final_report['unverified'])
check('早停-最终Stop放行', call('早停-完成Stop', ['hook'], json.dumps(loop))[1] == {})

# 从真实CLI验证记录保护，不能让后来的任务覆盖先前验收证据。
cp2, jp2, art2 = scenario('报告目录隔离')
rc, first = call('记录隔离-首次验收', ['score', cp2, jp2])
report_file = cp2.parent / 'work-eval-score.json'
original_report = report_file.read_bytes()
alias_contract = cp2.parent / 'other-contract.json'
alias_contract.write_bytes(cp2.read_bytes())
rc, _ = call('记录隔离-另一契约同目录', ['score', alias_contract, jp2])
check('不同契约拒绝覆盖原报告', rc == 2 and report_file.read_bytes() == original_report)
lock = cp2.parent / '.work-eval-write.lock'
lock.mkdir()
rc, _ = call('记录隔离-忙目录', ['score', cp2, jp2])
check('写锁阻止混写且不改原报告', rc == 2 and report_file.read_bytes() == original_report and lock.is_dir())
# 本例自己创建的空锁已完成用途，只移除这个明确的空目录。
lock.rmdir()
rc, _ = call('记录隔离-同契约顺序重验', ['score', cp2, jp2])
check('同契约顺序重验可用', rc == 0 and not lock.exists())
check('报告绑定精确契约路径', first.get('contract_path') == str(cp2.resolve()))

# 模拟安装器只复制一个技能，不能借安装父目录开启维护门禁。
installed = RUN / 'installed' / 'work-eval'
shutil.copytree(SCRIPT.parent.parent, installed)
installed_script = installed / 'scripts/work_eval.py'
cp, jp, artifact = scenario('独立安装输入', lambda c, j, a: j['reviewer'].update(kind='self'))
for label, args, expected_code, expected_status, stdin in [
    ('独立安装自检', ['score', cp, jp], 1, 'provisional', None),
    ('独立安装拒绝门禁', ['arm', cp, '--session', 'installed', '--turn', 'one', '--cwd', RUN], 2, None, None),
    ('独立安装跳过hook', ['hook'], 0, None, json.dumps({'hook_event_name': 'UserPromptSubmit', 'session_id': 'installed', 'turn_id': 'one', 'cwd': str(RUN)})),
]:
    command = [sys.executable, str(installed_script)] + [str(x) for x in args]
    result = subprocess.run(command, input=stdin, capture_output=True, text=True)
    save(RUN / (label + '.json'), {'command': command, 'stdin': stdin, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    value = json.loads(result.stdout) if result.stdout.strip() else {}
    check(label, result.returncode == expected_code and (value.get('status') == expected_status if expected_status else value == {}))
links_ok = True
for doc in installed.rglob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
        if target.startswith(('https:', 'http:', '#')):
            continue
        resolved = (doc.parent / target.split('#')[0]).resolve()
        links_ok = links_ok and resolved.is_relative_to(installed) and resolved.is_file()
check('独立安装必需文档自包含', links_ok)

check('回放期间实现版本一致', START_HASH == sha(SCRIPT))
check('回放期间回放脚本版本一致', START_REPLAY_HASH == sha(Path(__file__)))
summary = {'scope': '黑盒CLI与hook协议；合成案例不是业务评分', 'script_sha256': START_HASH,
           'replay_sha256': START_REPLAY_HASH, 'pass': all(x['pass'] for x in RESULTS), 'cases': RESULTS}
save(RUN / 'report.json', summary)
print(json.dumps({'report': str(RUN / 'report.json'), 'pass': summary['pass'], 'cases': len(RESULTS)}, ensure_ascii=False))
raise SystemExit(0 if summary['pass'] else 1)
