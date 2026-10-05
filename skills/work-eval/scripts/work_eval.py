"""把独立评审与实际工件绑定，必要失败项不由平均分放行。@author Pjh"""

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Union

PathLike = Union[str, Path]
PROJECT_ROOT = Path(__file__).resolve().parents[3]

RESERVED_ACTION_IDS = {"coverage", "integrity", "scope", "binding", "protocol"}


def action_key(item: dict[str, Any]) -> tuple[str, str]:
    """逐项匹配操作和精确目标，避免把笼统任务当作额外写入或发布权限。@author Pjh"""
    if not isinstance(item, dict) or item.get("operation") not in {"write", "delete", "execute", "install", "send", "publish"}:
        raise ValueError("操作须为write/delete/execute/install/send/publish")
    target = item.get("target")
    if not isinstance(target, str) or not target.strip():
        raise ValueError("操作target不能为空")
    if item["operation"] in {"write", "delete"} and (not Path(target).is_absolute() or str(Path(target).resolve()) != target):
        raise ValueError("文件操作target须为规范化绝对路径，不支持通配或别名")
    return item["operation"], target


def quote_matches(path: PathLike, quote: str, line: int = 0) -> bool:
    """按行读UTF-8正文核对片段；只证明文字存在，不证明它支持主张。@author Pjh"""
    try:
        with Path(path).open(encoding="utf-8") as stream:
            for number, content in enumerate(stream, 1):
                if (not line or number == line) and quote in content:
                    return True
                if line and number >= line:
                    break
    except (OSError, UnicodeError):
        pass
    return False


def parse_object(raw: bytes) -> dict[str, Any]:
    """读取对象并拒绝JSON非有限数值，避免伪造分数绕过检查。@author Pjh"""
    def reject(value: str) -> None:
        raise ValueError("JSON不接受非有限数值: " + value)
    data = json.loads(raw.decode("utf-8"), parse_constant=reject)
    if not isinstance(data, dict):
        raise ValueError("JSON顶层必须是对象")
    return data


def load(path: PathLike) -> dict[str, Any]:
    return parse_object(Path(path).read_bytes())


def digest(path: PathLike) -> str:
    """按块计算当前文件哈希，不把大工件内容打印到日志。@author Pjh"""
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: PathLike, value: dict[str, Any]) -> None:
    """原子替换单份状态，避免Stop读到半写入的JSON。@author Pjh"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def contract_data(path: PathLike) -> tuple[dict[str, Any], str]:
    """逐项验收以契约为准；遗漏或重复要求都不应默默放行。@author Pjh"""
    raw = Path(path).read_bytes()
    data = parse_object(raw)
    if data.get("task_type") not in {"code", "document", "computer", "research", "mixed"}:
        raise ValueError("task_type无效")
    for key in ("task_id", "goal"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(key + "不能为空")
    criteria = data.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise ValueError("criteria必须逐项列出")
    ids = []
    for item in criteria:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError("criterion id无效")
        if type(item.get("required")) is not bool or not isinstance(item.get("description"), str) or not item["description"].strip():
            raise ValueError("criterion缺少required或description")
        ids.append(item["id"])
    if len(ids) != len(set(ids)) or not any(c["required"] for c in criteria):
        raise ValueError("criterion重复或没有必要验收项")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("必须声明实际工件绝对路径")
    if any(not isinstance(p, str) or not Path(p).is_absolute() for p in artifacts):
        raise ValueError("artifacts必须是绝对路径")
    if len(artifacts) != len(set(artifacts)):
        raise ValueError("artifact路径重复")
    if data.get("request_artifact") not in artifacts:
        raise ValueError("request_artifact必须引用已声明的原始要求文件")
    version = data.get("schema_version", 2)
    if type(version) is not int or version not in {2, 3}:
        raise ValueError("schema_version须为2或3")
    if version == 3:
        if set(ids) & RESERVED_ACTION_IDS:
            raise ValueError("v3 criterion id不能占用系统核查动作ID")
        scope = data.get("scope")
        if not isinstance(scope, dict) or not isinstance(scope.get("allowed_actions"), list):
            raise ValueError("v3须声明scope.allowed_actions，纯只读可为空")
        keys = []
        for item in scope["allowed_actions"]:
            keys.append(action_key(item))
            quote = item.get("request_quote")
            if not isinstance(quote, str) or not quote.strip() or "\n" in quote:
                raise ValueError("允许操作须引用原要求的单行request_quote")
        if len(keys) != len(set(keys)):
            raise ValueError("允许操作重复")
    return data, hashlib.sha256(raw).hexdigest()


def evaluate(contract: PathLike, judgment: PathLike) -> dict[str, Any]:
    """状态由必要结果及证据决定，必要条件、证据和独立性另行判定。@author Pjh"""
    contract, judgment = Path(contract).resolve(), Path(judgment).resolve()
    c, contract_hash = contract_data(contract)
    judgment_raw = judgment.read_bytes()
    j = parse_object(judgment_raw)
    judgment_hash = hashlib.sha256(judgment_raw).hexdigest()
    hashes = {p: digest(p) if Path(p).is_file() else None for p in c["artifacts"]}
    allowed = set(hashes)
    reviewed_hashes = j.get("artifact_hashes")
    if not isinstance(reviewed_hashes, dict) or set(reviewed_hashes) != allowed:
        raise ValueError("评审者必须记录全部工件的当时哈希")
    reviewed_contract = j.get("contract_sha256")
    if not isinstance(reviewed_contract, str) or not re.fullmatch(r"[0-9a-f]{64}", reviewed_contract):
        raise ValueError("评审者必须记录评审时的契约SHA256")

    def non_request_file(path: str) -> bool:
        """按实际文件身份排除原请求，路径别名和软硬链接也不能冒充终态证据。@author Pjh"""
        if hashes[path] is None or hashes[c["request_artifact"]] is None:
            return False
        try:
            return not Path(path).samefile(c["request_artifact"])
        except OSError:
            return False

    def evidence(item: dict[str, Any], require: bool = False) -> bool:
        paths = item.get("evidence", [])
        if not isinstance(paths, list) or any(not isinstance(p, str) or p not in allowed for p in paths):
            raise ValueError("证据必须引用契约已声明的工件")
        # 原要求只说明用户要什么，不能单独证明已经做成或核对过实际操作。
        return (any(non_request_file(p) for p in paths) or not require) and all(hashes[p] is not None for p in paths)

    def reason(item: dict[str, Any]) -> None:
        if not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise ValueError("每项判断必须有具体理由")

    items = j.get("criteria")
    if not isinstance(items, list) or any(not isinstance(x, dict) for x in items):
        raise ValueError("评审必须逐项覆盖criteria")
    ids = [x.get("id") for x in items]
    if len(ids) != len(set(ids)) or set(ids) != {x["id"] for x in c["criteria"]}:
        raise ValueError("评审遗漏、重复或新增了验收项")
    failures, unknown = [], []
    coverage = j.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("status") not in {"pass", "fail", "unverified"}:
        raise ValueError("必须单独核对原要求覆盖coverage")
    reason(coverage)
    missing = coverage.get("missing_requirements")
    if not isinstance(missing, list) or any(not isinstance(x, str) or not x.strip() for x in missing):
        raise ValueError("missing_requirements必须逐项记录遗漏")
    actions = j.get("next_actions")
    if not isinstance(actions, list) or any(not isinstance(x, dict) or
            not isinstance(x.get("id"), str) or not x["id"] or
            not isinstance(x.get("action"), str) or not x["action"].strip() for x in actions):
        raise ValueError("next_actions必须记录缺口和具体下一动作")
    action_ids = {x["id"] for x in actions}

    def next_action(identifier: str, action: str) -> None:
        """机器发现具体缺口时保留对应动作，不自动执行输入中的建议。@author Pjh"""
        if identifier not in action_ids:
            actions.append({"id": identifier, "action": action})
            action_ids.add(identifier)
    if coverage["status"] != "pass" or missing:
        if "coverage" not in action_ids:
            raise ValueError("原要求覆盖缺口必须有下一动作")
        if coverage["status"] == "fail" or missing:
            failures.append("原要求覆盖: " + coverage["reason"] + "；" + "；".join(missing))
        else:
            unknown.append("原要求覆盖尚未核实")
    if reviewed_contract != contract_hash or digest(contract) != contract_hash:
        unknown.append("验收目标或要求已不同于评审者检查的契约")
    if reviewed_hashes != hashes:
        unknown.append("工件已不同于评审者检查的版本")
    if digest(judgment) != judgment_hash:
        unknown.append("评审文件在读取期间已变化")
    required = {x["id"] for x in c["criteria"] if x["required"]}
    for item in items:
        reason(item)
        if item.get("status") not in {"pass", "fail", "unverified"}:
            raise ValueError("criterion状态无效")
        supported = evidence(item, require=item["status"] == "pass")
        if item["status"] == "pass" and not supported:
            item["status"] = "unverified"
            item["reason"] += "；所引证据缺失，未确认通过"
            if item["id"] not in action_ids:
                actions.append({"id": item["id"], "action": "补齐该项实际证据后重新评审"})
                action_ids.add(item["id"])
        if item["id"] in required:
            if item["status"] != "pass" and item["id"] not in action_ids:
                raise ValueError("必要项缺口必须有下一动作: " + item["id"])
            if item["status"] == "fail":
                failures.append(item["id"] + ": " + item["reason"])
            elif item["status"] != "pass" or not supported:
                unknown.append(item["id"] + ": 未验证或证据缺失")
    integrity = j.get("integrity", {})
    if not isinstance(integrity, dict) or integrity.get("status") not in {"pass", "fail", "unverified"}:
        raise ValueError("integrity状态无效")
    reason(integrity)
    if integrity["status"] != "pass" and "integrity" not in action_ids:
        raise ValueError("真实性或权限缺口必须有下一动作")
    if integrity["status"] == "fail":
        failures.append("证据真实性/权限: " + integrity["reason"])
    elif integrity["status"] != "pass":
        unknown.append("证据真实性/权限尚未核实")
    elif not evidence(integrity, require=True):
        unknown.append("真实性/权限缺少实际核查证据")
        next_action("integrity", "读取实际差异和工具日志，补齐真实性及授权核查证据后重评")
    if c.get("schema_version", 2) != 3:
        unknown.append("旧协议未启用关键主张与操作范围核查")
        next_action("protocol", "按v3补齐关键主张来源、允许操作及实际操作核查后重评")
    else:
        claims = j.get("claims")
        if not isinstance(claims, list) or not claims:
            raise ValueError("v3须逐条记录关键claims，不能用空清单跳过")
        claim_ids = set()
        reserved = RESERVED_ACTION_IDS | set(ids)
        for item in claims:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip() or item["id"] in claim_ids or item["id"] in reserved:
                raise ValueError("claim id为空、重复或与验收/系统动作ID冲突")
            claim_ids.add(item["id"])
            if not isinstance(item.get("text"), str) or not item["text"].strip() or type(item.get("required")) is not bool:
                raise ValueError("claim须有text和布尔required")
            if item.get("kind") not in {"fact", "inference", "unknown"} or item.get("basis") not in {"observed", "inferred", "missing", "contradicted"}:
                raise ValueError("claim分类或依据无效")
            reason(item)
            sources = item.get("sources")
            if not isinstance(sources, list):
                raise ValueError("claim sources须为列表")
            supported = bool(sources)
            for source in sources:
                if not isinstance(source, dict) or source.get("artifact") not in allowed:
                    raise ValueError("来源须引用已声明工件")
                quote, line = source.get("quote"), source.get("line")
                if not isinstance(quote, str) or not quote.strip() or len(quote) > 1000 or "\n" in quote or type(line) is not int or not 1 <= line <= 100000:
                    raise ValueError("来源须有1到100000行号及不超过1000字的单行quote")
                supported = (non_request_file(source["artifact"])
                             and quote_matches(source["artifact"], quote, line)) and supported
            problem = None
            if (item["kind"] == "fact" and item["basis"] in {"inferred", "contradicted"}) or (item["kind"] == "inference" and item["basis"] == "contradicted"):
                failures.append(item["id"] + ": 推断冒充事实或主张与反证冲突")
                problem = "修正该主张，按来源明确事实、推断或未知，撤回与反证冲突的结论"
            elif (item["kind"] != "unknown" and (item["basis"] == "missing" or not supported)) or (item["required"] and (item["kind"] != "fact" or item["basis"] != "observed")):
                unknown.append(item["id"] + ": 主张缺可核对来源或必要结论仍不确定")
                problem = "补齐该主张的真实来源；无法证实则保留未知，并暂停依赖该结论的动作"
            if problem:
                next_action(item["id"], problem)
        scope = j.get("scope")
        if not isinstance(scope, dict) or scope.get("status") not in {"pass", "fail", "unverified"} or not isinstance(scope.get("actions"), list):
            raise ValueError("v3须有scope状态与实际actions列表")
        reason(scope)
        if scope["status"] != "pass" and "scope" not in action_ids:
            raise ValueError("范围缺口必须有下一动作")
        if scope["status"] == "fail":
            failures.append("操作范围: " + scope["reason"])
        elif scope["status"] == "unverified" or not evidence(scope, require=True):
            unknown.append("操作范围缺少实际差异或日志核查证据")
            next_action("scope", "对照原要求、实际差异和工具日志核对操作完整性，再重新评审")
        permitted = {action_key(x) for x in c["scope"]["allowed_actions"]}
        for item in c["scope"]["allowed_actions"]:
            if not quote_matches(c["request_artifact"], item["request_quote"]):
                unknown.append("允许操作的授权引文未在原要求中确认")
                next_action("scope", "对照用户原话修正授权依据；缺少真实授权时暂停对应操作")
        for item in scope["actions"]:
            if action_key(item) not in permitted:
                failures.append("未授权操作: " + item["operation"] + " " + item["target"])
                next_action("scope", "停止未授权操作，核对实际影响并在现有授权内修复；额外需求单独交用户决定")
    if any(h is None for h in hashes.values()):
        unknown.append("声明的工件不存在或不是文件")
    if unknown and "binding" not in action_ids:
        actions.append({"id": "binding", "action": "核对原要求、当前工件和版本缺口，读取实际对象后重新评审"})
    reviewer = j.get("reviewer", {})
    if not isinstance(reviewer, dict) or reviewer.get("kind") not in {"independent", "self"} or not isinstance(reviewer.get("id"), str) or not reviewer["id"].strip():
        raise ValueError("必须记录评审者kind和id")
    # 单独显示否决结果，不把主观平均分当成验收事实。
    status = "fail" if failures else "partial" if unknown else "provisional" if reviewer["kind"] == "self" else "pass"
    if reviewer["kind"] == "self" and "protocol" not in action_ids:
        actions.append({"id": "protocol", "action": "独立评审未完成；保留自检与阻碍记录，可用后读取当前工件，在新验收目录补做独立评审"})
    return {"schema_version": 3, "contract_path": str(Path(contract).resolve()), "task_id": c["task_id"], "goal": c["goal"], "task_type": c["task_type"],
            "status": status, "required_failures": failures,
            "coverage": coverage, "integrity": integrity, "claims": j.get("claims", []), "scope": j.get("scope"), "next_actions": actions,
            "unverified": unknown, "criteria": items, "reviewer": reviewer,
            "artifact_hashes": hashes, "contract_sha256": contract_hash, "judgment_sha256": judgment_hash,
            "judgment_path": str(judgment), "verification_scope": "结构、版本、正文引文及已声明操作匹配；语义支持和记录完整性仍需独立阅读，身份标签不是认证"}


def score(contract: PathLike, judgment: PathLike) -> dict[str, Any]:
    """一个目录只允许同一契约顺序写报告，避免其他任务或并发进程混写证据。@author Pjh"""
    contract = Path(contract).resolve()
    lock = contract.parent / ".work-eval-write.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError("验收目录正在写入或留有中断锁；请用独立运行目录，勿覆盖或自动删除未知锁") from exc
    try:
        previous = contract.parent / "work-eval-score.json"
        if previous.exists() and load(previous).get("contract_path") != str(contract):
            raise ValueError("已有报告属于另一契约或旧格式无法确认归属；请在独立运行目录重新验收")
        return save_score(contract, judgment)
    finally:
        # 仅释放本次成功取得的空锁目录，不接管其他运行的锁。
        lock.rmdir()


def save_score(contract: PathLike, judgment: PathLike) -> dict[str, Any]:
    """保存机器汇总与可读报告，失败也留证据而非只打印一个分数。@author Pjh"""
    report = evaluate(contract, judgment)
    path = Path(contract).resolve().parent
    write_json(path / "work-eval-score.json", report)
    lines = ["<!-- @author Pjh -->", "# 逐项工作验收", "", "任务：" + report["goal"],
             "", "结果：**" + report["status"] + "**。完成由必要要求及其证据决定。",
             "", ("评审状态：**独立评审未完成**。以下为作者自检，必要项自检通过不代表整体验收完成。"
                    if report["reviewer"]["kind"] == "self" else "评审状态：已提供独立评审记录；身份标签本身不构成认证。"),
             "", "| 验收项 | 状态 | 判断依据 |", "| --- | --- | --- |"]
    # 报告直接呈现实际逐项判断；不再计算或输出旧五维分数。
    for item in report["criteria"]:
        cells = [str(item[key]).replace("|", "\\|").replace("\n", " ") for key in ("id", "status", "reason")]
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "必要失败项："] + (["- " + x for x in report["required_failures"]] or ["无。"])
    lines += ["", "必要项证据缺口（不含上述独立评审状态）："] + (["- " + x for x in report["unverified"]] or ["当前记录未列出证据缺口。"])
    lines += ["", "关键主张（分类与依据由评审者提供）："] + (
        ["- " + x["id"] + "：" + x["kind"] + " / " + x["basis"] + "；" + x["text"] for x in report["claims"]] or ["旧格式没有主张核查。"])
    scope = report["scope"]
    lines += ["", "操作范围核查：", scope["status"] + "；" + scope["reason"] if scope else "旧格式没有范围核查。"]
    if scope:
        lines += ["- " + x["operation"] + "：" + x["target"] for x in scope["actions"]]
    lines += ["", "下一动作："] + (["- " + x["id"] + ": " + x["action"] for x in report["next_actions"]] or ["无评审者记录的内容缺口；版本变化需重新读取工件并重评。"])
    lines += ["", "评审者：" + report["reviewer"]["id"], "", report["verification_scope"],
              "", "证据及理由详见同目录work-eval-score.json；文件变化后重新核验。"]
    (path / "work-eval-score.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def maintenance_scope(cwd: PathLike) -> bool:
    """仅完整维护仓库开放门禁，独立技能安装不能把父目录当作项目。@author Pjh"""
    source = PROJECT_ROOT / 'skills' / 'work-eval' / 'scripts' / 'work_eval.py'
    return ((PROJECT_ROOT / '.agent-workflow-root').is_file()
            and source.resolve() == Path(__file__).resolve()
            and Path(cwd).resolve().is_relative_to(PROJECT_ROOT))


def state_path(cwd: PathLike, session: str) -> Path:
    """按会话隔离，避免一个任务的评分门禁影响其他会话。@author Pjh"""
    if not isinstance(session, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", session):
        raise ValueError("session id无效")
    cwd = Path(cwd).resolve()
    if not maintenance_scope(cwd):
        raise ValueError("登记与状态仅允许在agent-workflow项目内")
    # 状态与任务记录统一保存在启动目录的.codex内，写入失败由调用方明确报告。
    path = cwd / ".codex" / "work-eval" / session / "active.json"
    if not path.resolve().is_relative_to(cwd):
        raise ValueError("评分状态路径越出会话目录")
    return path


def hook(event: dict[str, Any]) -> dict[str, Any]:
    """提示所有实质交付，Stop仅复核当前已登记任务并最多续跑一次。@author Pjh"""
    name = event.get("hook_event_name")
    session, turn, cwd = event.get("session_id"), event.get("turn_id"), event.get("cwd")
    # 即使误接入其他宿主目录，也不注入提示、不创建状态、不影响其他会话。
    if not isinstance(cwd, str) or not maintenance_scope(cwd):
        return {}
    if name == "UserPromptSubmit":
        prompt_path = state_path(cwd, session)
        if not prompt_path.is_file():
            return {}
        prompt_state = load(prompt_path)
        if prompt_state.get("session_id") != session or prompt_state.get("turn_id") != turn or prompt_state.get("release"):
            return {}
        return {"hookSpecificOutput": {"hookEventName": name, "additionalContext":
                "实质代码/文档/电脑操作/研究交付使用work-eval：执行前登记用户验收，交付前独立评审并运行评分脚本。简短问答、状态、确认可跳过。"
                + "当前评分session=" + str(session) + "，turn=" + str(turn) + "，启动cwd=" + str(cwd)
                + "。Stop只检查已登记任务；失败仍可推进则继续，真实阻碍/用户停止/硬预算保存未完成退出。"}}
    if name != "Stop" or not isinstance(turn, str) or not cwd:
        return {}
    path = state_path(cwd, session)
    if not path.is_file():
        return {}
    state = load(path)
    if state.get("session_id") != session or state.get("turn_id") != turn:
        return {}
    if state.get("release"):
        return {"systemMessage": "工作验收：已记录未完成退出（" + state["release"]["kind"] + "）；不代表验收通过。"}
    problem = None
    try:
        report_path = Path(state["contract"]).parent / "work-eval-score.json"
        report = load(report_path)
        expected = evaluate(state["contract"], report["judgment_path"])
        if expected["contract_sha256"] != state.get("contract_sha256"):
            problem = "登记后的验收契约已变化，需要核对最新授权并重新登记"
        elif report != expected:
            problem = "评分或工件已变化，需要重评"
        elif report["status"] != "pass":
            problem = "评分状态为" + report["status"] + "，必要条件未全部通过"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        problem = "缺少有效评分（" + type(exc).__name__ + "）"
    if problem is None:
        return {}
    if event.get("stop_hook_active") or state.get("continuations", 0) >= 1:
        return {"systemMessage": "AI工作评分未通过：" + problem + "。续跑次数已达到1；保留未完成状态，不能声称完成。"}
    state["continuations"] = 1
    write_json(path, state)
    return {"decision": "block", "reason": "AI工作评分门禁：" + problem + "。使用work-eval核对" + state["contract"]
            + "。必要失败项仍可推进则修复并重评；真实外部阻碍、用户停止或硬预算达到时用release记录未完成原因。遵守已有权限，不自行扩大任务。"}


def main() -> int:
    """提供登记、评分、退出及原生hook入口，不执行输入里的命令。@author Pjh"""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    arm = sub.add_parser("arm")
    arm.add_argument("contract", type=Path)
    arm.add_argument("--session", default=os.environ.get("CODEX_THREAD_ID"))
    arm.add_argument("--turn", required=True)
    arm.add_argument("--cwd", type=Path, default=Path.cwd())
    scoring = sub.add_parser("score")
    scoring.add_argument("contract", type=Path)
    scoring.add_argument("judgment", type=Path)
    release = sub.add_parser("release")
    release.add_argument("--session", default=os.environ.get("CODEX_THREAD_ID"))
    release.add_argument("--turn", required=True)
    release.add_argument("--cwd", type=Path, default=Path.cwd())
    release.add_argument("--reason", choices=["user_stop", "external_block", "hard_budget"], required=True)
    release.add_argument("--detail", required=True)
    sub.add_parser("hook")
    args = parser.parse_args()
    try:
        if args.action == "hook":
            event = json.load(sys.stdin)
            if not isinstance(event, dict):
                raise ValueError("hook输入必须是JSON对象")
            result = hook(event)
        elif args.action == "arm":
            _, contract_hash = contract_data(args.contract)
            if not args.turn.strip():
                raise ValueError("turn不能为空")
            path = state_path(args.cwd, args.session)
            previous = load(path) if path.is_file() else {}
            same_turn = previous.get("session_id") == args.session and previous.get("turn_id") == args.turn
            continuations = previous.get("continuations", 0) if same_turn else 0
            write_json(path, {"session_id": args.session, "turn_id": args.turn,
                       "contract": str(args.contract.resolve()), "contract_sha256": contract_hash,
                       "continuations": continuations})
            result = {"armed": True, "session": args.session, "turn": args.turn}
        elif args.action == "release":
            path = state_path(args.cwd, args.session)
            state = load(path)
            if state.get("turn_id") != args.turn or not args.detail.strip():
                raise ValueError("退出需匹配当前turn并说明原因")
            state["release"] = {"kind": args.reason, "detail": args.detail}
            write_json(path, state)
            result = {"released_unfinished": True, "reason": args.reason}
        else:
            result = score(args.contract, args.judgment)
        print(json.dumps(result, ensure_ascii=False))
        return 1 if args.action == "score" and result["status"] != "pass" else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        if args.action == "hook":
            print(json.dumps({"systemMessage": "AI评分hook检查失败，未确认通过：" + type(exc).__name__}, ensure_ascii=False))
            return 0
        print(json.dumps({"error": type(exc).__name__, "detail": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
