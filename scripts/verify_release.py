"""只读核对发布清单及 Markdown 文件引用，避免源码存在却漏入分发；不验证锚点或运行效果。@author Pjh"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


def main():
    """按实际根目录解析清单与链接，先拒绝越界再读取文件，输出可保存的检查结果。@author Pjh"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path, help='被检查的源码根目录')
    parser.add_argument('--manifest', required=True, type=Path, help='发布清单；相对路径按 root 解析')
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = args.manifest if args.manifest.is_absolute() else root / args.manifest
    report = {'scope': '清单文件存在及 Markdown 本地文件引用闭包；不检查锚点、远端安装或模型效果',
              'root': str(root), 'manifest': str(manifest), 'release_entries': 0,
              'local_links_checked': 0, 'errors': []}
    errors = report['errors']
    exit_code = 0
    files = {}
    try:
        if not root.is_dir():
            raise OSError('源码根目录不存在或不是目录')
        lines = manifest.read_text(encoding='utf-8').splitlines()
        entries = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith('#')]
        report['release_entries'] = len(entries)
        if not entries:
            errors.append({'kind': 'empty_manifest', 'source': str(manifest)})
        for entry in entries:
            path = (root / entry).resolve()
            if Path(entry).is_absolute() or not path.is_relative_to(root):
                errors.append({'kind': 'outside_root', 'source': entry})
            elif not path.is_file():
                errors.append({'kind': 'missing_file', 'source': entry})
            else:
                files[path] = entry
        for path, entry in files.items():
            if path.suffix.lower() != '.md':
                continue
            for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                for match in re.finditer(r'!?\[[^\]]*\]\(\s*(<[^>]+>|[^)\n]+)\)', line):
                    target = match.group(1).strip()
                    if target.startswith('<'):
                        target = target[1:-1]
                    else:
                        target = re.split(r'\s+[\"\']', target, maxsplit=1)[0]
                    url = urlsplit(target)
                    if url.scheme or url.netloc or not url.path:
                        continue
                    report['local_links_checked'] += 1
                    local = unquote(url.path)
                    resolved = (path.parent / local).resolve()
                    evidence = {'source': entry, 'line': number, 'target': local}
                    if Path(local).is_absolute() or not resolved.is_relative_to(root):
                        errors.append({'kind': 'outside_root', **evidence})
                    elif not resolved.exists():
                        errors.append({'kind': 'missing_target', **evidence})
                    elif resolved.is_file() and resolved not in files:
                        errors.append({'kind': 'not_in_manifest', **evidence})
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append({'kind': 'read_error', 'reason': str(exc)})
        exit_code = 2
    if errors and not exit_code:
        exit_code = 1
    report['status'] = 'pass' if exit_code == 0 else 'error' if exit_code == 2 else 'fail'
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
