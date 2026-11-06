# @author Pjh：用真实CLI和hook输入回放记录处理。

import argparse
import copy
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


def save(path: Path, value: dict) -> None:
    """保留输入与输出，便于独立重放。@author Pjh"""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


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
    if channel == 'claims':
        j['claims'][0]['sources'] = [{'artifact': alias, 'line': 1, 'quote': '写入合成协议工件'}]
    elif channel == 'criteria':
        j['criteria'][0]['evidence'] = [alias]
    else:
        j[channel]['evidence'] = [alias]


class Replay:
    """保存一轮回放的脚本位置、产物目录与断言。@author Pjh"""

    def __init__(self, script: Path, run: Path) -> None:
        """接收本轮脚本路径与独立产物目录。@author Pjh"""
        self.script = script
        self.run = run
        self.results = []

    def call(self, label: str, args: list[Union[str, Path]], stdin: Optional[str] = None,
             script: Optional[Path] = None, expected_codes: Optional[set[int]] = None) -> tuple:
        """共用真实调用、原始日志与解析，独立安装显式选择脚本和预期退出码。@author Pjh"""
        command = [sys.executable, str(script or self.script)] + [str(x) for x in args]
        result = subprocess.run(command, input=stdin, capture_output=True, text=True)
        save(self.run / (label + '.json'), {'command': command, 'stdin': stdin,
             'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        if expected_codes is None and args[0] != 'score':
            expected_codes = {0}
        if expected_codes is not None and result.returncode not in expected_codes:
            raise RuntimeError(label + ': 命令失败，见本例日志')
        value = json.loads(result.stdout) if result.stdout.strip() else {}
        return result.returncode, value

    def check(self, label: str, condition: bool) -> None:
        """累计真实断言，失败保留到本轮报告并使进程非零退出。@author Pjh"""
        self.results.append({'case': label, 'pass': bool(condition)})

    def scenario(self, name: str, edit: FixtureEdit = None) -> tuple:
        """为每个案例创建独立输入与文件。@author Pjh"""
        folder = self.run / name
        folder.mkdir()
        artifact = folder / '实际工件.txt'
        artifact.write_text('本例合成协议工件。\n', encoding='utf-8')
        request = folder / '原始要求.txt'
        request.write_text('本例要求：写入合成协议工件并核验内容。\n', encoding='utf-8')
        contract = {'schema_version': 4, 'task_id': name, 'task_type': 'mixed', 'goal': '合成协议回放',
                    'criteria': [{'id': 'C1', 'description': '本例必要项', 'required': True}],
                    'scope': {'allowed_actions': [{'operation': 'write', 'target': str(artifact),
                              'request_quote': '写入合成协议工件并核验内容'}]},
                    'request_artifact': str(request), 'artifacts': [str(artifact), str(request)]}
        cp, jp = folder / 'contract.json', folder / 'judgment.json'
        save(cp, contract)
        proof = [str(artifact)]
        judgment = {'reviewer': {'kind': 'independent', 'id': 'synthetic-protocol-fixture'},
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
                judgment['next_actions'].append({'id': 'coverage', 'action': '核对原要求并修订任务要求文件后重评'})
        save(cp, contract)
        save(jp, judgment)
        return cp, jp, artifact

    def score_case(self, name: str, edit: FixtureEdit, code: int, status: Optional[str] = None,
                   expected_actions: Optional[set[str]] = None) -> tuple:
        """通过真实 score 调用核对本例状态及原下一动作。@author Pjh"""
        cp, jp, artifact = self.scenario(name, edit)
        rc, report = self.call(name, ['score', cp, jp])
        self.check(name, rc == code and (status is None or report.get('status') == status))
        if expected_actions is not None:
            actions = report.get('next_actions', [])
            original = json.loads(jp.read_text(encoding='utf-8'))['next_actions']
            self.check(name + '-下一动作准确且保留原判断', {x['id'] for x in actions} == expected_actions
                  and all(x in actions for x in original) and len(actions) == len(expected_actions))
        return cp, jp, artifact, report


def run_score(replay: Replay) -> tuple:
    """核验记录检查及报告隔离，不登记门禁或复制安装目录。@author Pjh"""
    call, check = replay.call, replay.check
    scenario, score_case = replay.scenario, replay.score_case

    success = score_case('成功', None, 0, 'pass', set())
    check('无摘要输入实际可用', success[3].get('schema_version') == 4
          and all('sha256' not in key and key != 'artifact_hashes'
                  for record in [json.loads(success[0].read_text(encoding='utf-8')),
                                 json.loads(success[1].read_text(encoding='utf-8')), success[3]] for key in record))
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
    score_case('同ID说明变化仅检查当前记录', lambda c, j, a: c.update(goal='修改后的目标'), 0, 'pass', set())
    score_case('来源正文已变', lambda c, j, a: a.write_text('变化的版本', encoding='utf-8'), 1, 'partial', {'F1'})
    score_case('v3记录仍可读取', lambda c, j, a: c.update(schema_version=3), 0, 'pass')

    def missing(c: dict, j: dict, artifact: Path) -> None:
        """声明尚未创建的文件，用于验证缺失状态。@author Pjh"""
        path = str(artifact.parent / '未生成工件.txt')
        c['artifacts'].append(path)
        save(artifact.parent / 'contract.json', c)

    score_case('缺失文件', missing, 1, 'partial', {'binding'})
    score_case('声明目录不是文件', lambda c, j, a: c['artifacts'].append(str(a.parent)), 1, 'partial', {'binding'})
    score_case('现场未验证兼工件缺失', lambda c, j, a: (j['criteria'][0].update(status='unverified'),
               missing(c, j, a)), 1, 'partial', {'C1', 'binding'})
    score_case('必要失败兼工件缺失', lambda c, j, a: (j['criteria'][0].update(status='fail'),
               missing(c, j, a)), 1, 'fail', {'C1', 'binding'})
    score_case('保留已有binding动作', lambda c, j, a: (missing(c, j, a),
               j['next_actions'].append({'id': 'binding', 'action': '按原判断核对失效工件后重评'})), 1, 'partial', {'binding'})

    def optional(c: dict, j: dict, artifact: Path) -> None:
        c['criteria'].append({'id': 'O1', 'description': '可选项', 'required': False})
        save(artifact.parent / 'contract.json', c)
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
    score_case('原请求授权引文已变', lambda c, j, a: Path(c['request_artifact']).write_text('新原要求', encoding='utf-8'), 1, 'partial', {'scope'})
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
    binary = score_case('引用非UTF8正文', lambda c, j, a: a.write_bytes(b'\xff\xfe'), 1, 'partial', {'F1'})
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
    authorization = score_case('授权引文不存在', lambda c, j, a: c['scope']['allowed_actions'][0].update(request_quote='顺便安装软件并发布'), 1, 'partial', {'scope'})
    check('授权引文缺失原因准确', any('授权引文' in x for x in authorization[3].get('unverified', [])))
    legacy = score_case('旧协议不能绕过新核查', lambda c, j, a: (c.pop('schema_version'), c.pop('scope'), j.pop('claims'), j.pop('scope')), 1, 'partial', {'protocol'})
    check('旧格式缺新核查原因准确', any('旧协议' in x for x in legacy[3].get('unverified', [])))
    for mode in ['alias', 'symlink', 'hardlink']:
        score_case('请求同文件冒用-' + mode, lambda c, j, a, mode=mode: request_alias(c, j, a, mode), 1, 'partial', {'C1'})
    for channel in ['claims', 'integrity', 'scope']:
        score_case('请求链接冒用-' + channel, lambda c, j, a, channel=channel: request_alias(c, j, a, 'symlink', channel), 1, 'partial', {'F1' if channel == 'claims' else channel})
    for identifier in ['scope', 'integrity', 'binding', 'C1']:
        score_case('主张ID与动作冲突-' + identifier, lambda c, j, a, identifier=identifier: j['claims'][0].update(id=identifier), 2)
    score_case('验收ID与动作冲突', lambda c, j, a: (c['criteria'][0].update(id='scope'), j['criteria'][0].update(id='scope')), 2)

    # 用真实CLI验证不同输入和并发写入的报告隔离。
    cp2, jp2, art2 = scenario('报告目录隔离')
    rc, first = call('记录隔离-首次验收', ['score', cp2, jp2])
    report_file = cp2.parent / 'work-eval-score.json'
    original_report = report_file.read_bytes()
    alias_contract = cp2.parent / 'other-contract.json'
    alias_contract.write_bytes(cp2.read_bytes())
    rc, _ = call('记录隔离-另一输入同目录', ['score', alias_contract, jp2])
    check('不同输入拒绝覆盖原报告', rc == 2 and report_file.read_bytes() == original_report)
    lock = cp2.parent / '.work-eval-write.lock'
    lock.mkdir()
    rc, _ = call('记录隔离-忙目录', ['score', cp2, jp2])
    check('写锁阻止混写且不改原报告', rc == 2 and report_file.read_bytes() == original_report and lock.is_dir())
    # 本例自己创建的空锁已完成用途，只移除这个明确的空目录。
    lock.rmdir()
    rc, _ = call('记录隔离-同一输入顺序重验', ['score', cp2, jp2])
    check('同一输入顺序重验可用', rc == 0 and not lock.exists())
    check('报告绑定精确输入路径', first.get('contract_path') == str(cp2.resolve()))

    return success

def run_hook(replay: Replay, success: Optional[tuple] = None) -> None:
    """沿原顺序回放门禁隔离与历史早停连续链，单独运行仅建立必要成功前置。@author Pjh"""
    run = replay.run
    call, check = replay.call, replay.check
    scenario = replay.scenario

    if success is None:
        cp, jp, artifact = scenario('hook前置成功')
        rc, report = call('hook前置成功', ['score', cp, jp])
        check('hook前置成功', rc == 0 and report.get('status') == 'pass')
        success = cp, jp, artifact, report

    cwd = run / '独立会话'
    cwd.mkdir()
    event = {'hook_event_name': 'Stop', 'session_id': 'protocol-test', 'turn_id': 'turn-1', 'cwd': str(cwd)}
    cp, jp, artifact, report = success
    call('登记成功', ['arm', cp, '--session', event['session_id'], '--turn', event['turn_id'], '--cwd', cwd])
    state_without_digest = json.loads((cwd / '.codex/work-eval/protocol-test/active.json').read_text(encoding='utf-8'))
    check('登记状态不输出摘要', not any('sha256' in key or key == 'artifact_hashes' for key in state_without_digest))
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
    check('缺评分二次停止续跑', 'decision' not in call('无评分二次Stop', ['hook'], json.dumps(event))[1])
    call('未完成退出', ['release', '--session', event['session_id'], '--turn', event['turn_id'], '--cwd', cwd,
                      '--reason', 'external_block', '--detail', '本例模拟环境缺失'])
    check('退出不伪称通过', '未完成退出' in call('退出Stop', ['hook'], json.dumps(event))[1].get('systemMessage', ''))
    rc, result = call('非对象hook', ['hook'], '[]')
    check('非对象hook返回错误', rc == 0 and 'ValueError' in result.get('systemMessage', '') and 'decision' not in result)
    rc, result = call('坏JSONhook', ['hook'], '{')
    check('坏JSONhook返回错误', rc == 0 and 'JSONDecodeError' in result.get('systemMessage', '') and 'decision' not in result)
    prompt = dict(event, hook_event_name='UserPromptSubmit')
    check('退出后Prompt不注入', call('退出后Prompt', ['hook'], json.dumps(prompt))[1] == {})
    call('恢复实验登记', ['arm', no_score, '--session', event['session_id'], '--turn', event['turn_id'], '--cwd', cwd])
    check('Prompt注入真实轮次', 'turn-2' in call('Prompt触发', ['hook'], json.dumps(prompt))[1]['hookSpecificOutput']['additionalContext'])
    check('新轮无重登记不注入', call('新轮Prompt', ['hook'], json.dumps(dict(prompt, turn_id='turn-3')))[1] == {})
    foreign = dict(event, cwd=str(PROJECT.parent / 'skills-external-check'), hook_event_name='UserPromptSubmit')
    check('项目外Prompt无注入', call('项目外Prompt', ['hook'], json.dumps(foreign))[1] == {})
    foreign['hook_event_name'] = 'Stop'
    check('项目外Stop无拦截', call('项目外Stop', ['hook'], json.dumps(foreign))[1] == {})

    # 用历史反馈中的三个缺口构造连续恢复案例。
    cp, jp, artifact = scenario('历史早停闭环')
    c, j = json.loads(cp.read_text(encoding='utf-8')), json.loads(jp.read_text(encoding='utf-8'))
    request = Path(c['request_artifact'])
    request.write_text('本例要求：写入合成协议工件并核验内容。\n'
                       'R006、视觉第2页、视觉第3页是三个必要项，全部通过才完成。\n', encoding='utf-8')
    c['criteria'] = [{'id': identifier, 'description': description, 'required': True} for identifier, description in
                     [('R006', '合成R006终态'), ('V002', '合成视觉第2页终态')]]
    j['criteria'] = [{'id': item['id'], 'status': 'unverified', 'reason': '合成未识别状态，仍需回修',
                      'evidence': [str(artifact)]} for item in c['criteria']]
    j['coverage'].update(status='fail', reason='原要求中的视觉第3页漏列', missing_requirements=['视觉第3页'])
    j['next_actions'] = [{'id': 'R006', 'action': '定位合成R006未识别原因并验证'},
                         {'id': 'V002', 'action': '补核合成视觉第2页'},
                         {'id': 'coverage', 'action': '补回原要求中的视觉第3页并验收'}]
    save(cp, c)
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
    rejected_log = json.loads((run / '早停-补要求但沿用旧评审.json').read_text(encoding='utf-8'))
    rejected = json.loads(rejected_log['stderr'])
    check('早停-新增必要项须重评', rc == 2 and '评审遗漏、重复或新增了验收项' in rejected.get('detail', ''))
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

    loop_cwd = run / '历史早停会话'
    loop_cwd.mkdir()
    loop = {'hook_event_name': 'Stop', 'session_id': 'closed-loop', 'turn_id': 'before-resume', 'cwd': str(loop_cwd)}
    call('早停-登记第一轮', ['arm', cp, '--session', loop['session_id'], '--turn', loop['turn_id'], '--cwd', loop_cwd])
    check('早停-未完成请求继续', call('早停-首次Stop', ['hook'], json.dumps(loop))[1].get('decision') == 'block')
    warning = call('早停-第二次Stop', ['hook'], json.dumps(loop))[1]
    check('早停-续跑耗尽保留未完成', 'decision' not in warning and '未完成状态' in warning.get('systemMessage', ''))
    loop['turn_id'] = 'after-resume'
    check('早停-新轮不猜旧任务', call('早停-新轮未登记Stop', ['hook'], json.dumps(loop))[1] == {})
    call('早停-明确恢复原任务', ['arm', cp, '--session', loop['session_id'], '--turn', loop['turn_id'], '--cwd', loop_cwd])
    state = json.loads((loop_cwd / '.codex/work-eval/closed-loop/active.json').read_text(encoding='utf-8'))
    save(cp.parent / '恢复登记快照.json', state)
    check('早停-恢复关联同一输入', state['contract'] == str(cp.resolve())
          and state['turn_id'] == 'after-resume' and state['continuations'] == 0)
    check('早停-恢复后旧缺口仍拦', call('早停-恢复Stop', ['hook'], json.dumps(loop))[1].get('decision') == 'block')

    artifact.write_text(artifact_initial + '模拟回修：R006=pass，V002和V003仍未验证。\n', encoding='utf-8')
    (cp.parent / '工件-部分回修.txt').write_bytes(artifact.read_bytes())
    rc, stale = call('早停-回修工件但旧评审', ['score', cp, pending])
    check('早停-当前记录缺口仍保留', rc == 1 and stale.get('status') == 'partial'
          and {'R006', 'V002', 'V003'} <= {x['id'] for x in stale['next_actions']})
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

    artifact.write_text(artifact_initial + '模拟回修：R006、V002、V003均为pass。\n', encoding='utf-8')
    (cp.parent / '工件-全部回修.txt').write_bytes(artifact.read_bytes())
    for item in j['criteria']:
        item.update(status='pass', reason='合成终态已核验')
    j['next_actions'] = []
    final_judgment = cp.parent / 'judgment-全部回修.json'
    save(final_judgment, j)
    rc, final_report = call('早停-全部回修后重评', ['score', cp, final_judgment])
    check('早停-全部必要项满足才通过', rc == 0 and final_report.get('status') == 'pass'
          and all(x['status'] == 'pass' for x in final_report['criteria'])
          and not final_report['required_failures'] and not final_report['unverified'])
    check('早停-最终Stop放行', call('早停-完成Stop', ['hook'], json.dumps(loop))[1] == {})


def run_installed(replay: Replay) -> None:
    """只在本轮任务目录复制技能，核验独立自检和维护门禁拒绝。@author Pjh"""
    run = replay.run
    call, check = replay.call, replay.check
    scenario = replay.scenario

    # 独立安装副本按技能目录复制，维护范围按真实根标记验证。
    installed = run / 'installed' / 'work-eval'
    shutil.copytree(replay.script.parent.parent, installed)
    installed_script = installed / 'scripts/work_eval.py'
    cp, jp, artifact = scenario('独立安装输入', lambda c, j, a: j['reviewer'].update(kind='self'))
    for label, args, expected_code, expected_status, stdin in [
        ('独立安装自检', ['score', cp, jp], 1, 'provisional', None),
        ('独立安装拒绝门禁', ['arm', cp, '--session', 'installed', '--turn', 'one', '--cwd', run], 2, None, None),
        ('独立安装跳过hook', ['hook'], 0, None, json.dumps({'hook_event_name': 'UserPromptSubmit', 'session_id': 'installed', 'turn_id': 'one', 'cwd': str(run)})),
    ]:
        rc, value = call(label, args, stdin, script=installed_script, expected_codes={expected_code})
        check(label, rc == expected_code and (value.get('status') == expected_status if expected_status else value == {}))
    links_ok = True
    for doc in installed.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if target.startswith(('https:', 'http:', '#')):
                continue
            resolved = (doc.parent / target.split('#')[0]).resolve()
            links_ok = links_ok and resolved.is_relative_to(installed) and resolved.is_file()
    check('独立安装必需文档自包含', links_ok)


def main(argv: Optional[list[str]] = None) -> int:
    """解析选择后创建本轮上下文，默认完整保留全部既有回放。@author Pjh"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['all', 'score', 'hook', 'installed'], default='all',
                        help='选择回放分组；默认 all 执行全部既有案例')
    args = parser.parse_args(argv)
    root = Path.cwd() / '.codex' / 'verification'
    run = root / ('协议回放-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    run.mkdir(parents=True)
    replay = Replay(PROJECT / 'skills' / 'work-eval' / 'scripts' / 'work_eval.py', run)
    success = run_score(replay) if args.suite in {'all', 'score'} else None
    if args.suite in {'all', 'hook'}:
        run_hook(replay, success)
    if args.suite in {'all', 'installed'}:
        run_installed(replay)
    scopes = {
        'all': '合成输入的真实CLI回放：记录处理、局部hook和独立技能副本',
        'score': '合成输入的真实score记录处理与报告目录隔离',
        'hook': '合成输入的真实局部hook、score前置和连续恢复链回放',
        'installed': '任务目录内独立技能副本的score、维护范围和本地引用检查',
    }
    summary = {'scope': scopes[args.suite], 'suite': args.suite,
               'pass': all(x['pass'] for x in replay.results), 'cases': replay.results}
    save(run / 'report.json', summary)
    print(json.dumps({'report': str(run / 'report.json'), 'pass': summary['pass'],
                      'cases': len(replay.results), 'suite': args.suite}, ensure_ascii=False))
    return 0 if summary['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
