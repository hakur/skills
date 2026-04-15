"""L2 Standards Compliance - Mechanical rule checking via regex"""
import os
import re
import sys
from typing import List, Dict, Any


CHECKS = [
    {
        "id": "FORBIDDEN_MUTEX",
        "pattern": r"sync\.(Mutex|RWMutex)\b",
        "include": r"\.go$",
        "exclude": r"vendor/",
        "message": "禁止使用 sync.Mutex/sync.RWMutex, 请使用 deadlock.Mutex/deadlock.RWMutex",
        "severity": "ERROR",
    },
    {
        "id": "FORBIDDEN_LOGGER_INSTANCE",
        "pattern": r"(logrus\.(New\(\))|zap\.(New\(\)|NewLogger\(\)|NewConfig\(\)|NewDevelopmentConfig\(\)|NewProductionConfig\(\)))",
        "include": r"\.go$",
        "exclude": r"vendor/",
        "message": "禁止创建日志库新实例, 请使用全局方法如 logrus.Info()",
        "severity": "ERROR",
    },
    {
        "id": "FORBIDDEN_LOGGER_REGISTER",
        "pattern": r"logrus\.Register\(\)",
        "include": r"\.go$",
        "exclude": r"vendor/",
        "message": "禁止调用 logrus.Register()",
        "severity": "ERROR",
    },
    {
        "id": "FORBIDDEN_NESTED_TEST",
        "pattern": r"t\.Run\(",
        "include": r"_test\.go$",
        "exclude": r"vendor/",
        "message": "禁止在测试中使用 t.Run 嵌套",
        "severity": "ERROR",
    },
    {
        "id": "FORBIDDEN_TEST_SKIP",
        "pattern": r"t\.Skip",
        "include": r"_test\.go$",
        "exclude": r"vendor/",
        "message": "禁止使用 t.Skip, 请补充测试条件",
        "severity": "ERROR",
    },
    {
        "id": "FORBIDDEN_INTEGRATION_TEST",
        "pattern": r"_integration_test\.go$",
        "include": r"\.go$",
        "exclude": r"vendor/",
        "match_filename": True,
        "message": "禁止生成 xxx_integration_test.go",
        "severity": "ERROR",
    },
    {
        "id": "FORBIDDEN_GORILLA_WEBSOCKET",
        "pattern": r"gorilla/websocket",
        "include": r"\.go$",
        "exclude": r"vendor/",
        "message": "禁止使用 gorilla/websocket, 请使用 coder/websocket",
        "severity": "ERROR",
    },
    {
        "id": "FORBIDDEN_MEANINGLESS_INTERFACE",
        "pattern": r"type\s+(Default|Basic|Standard|Normal|Plain|Impl\d*|Implementation|Generic)\w*\s+interface",
        "include": r"\.go$",
        "exclude": r"vendor/",
        "message": "禁止使用无意义命名如 DefaultInterface，请使用语义化命名",
        "severity": "WARN",
    },
    {
        "id": "FORBIDDEN_MEANINGLESS_STRUCT",
        "pattern": r"type\s+((Default|Basic|Standard|Normal|Plain|Generic)\w*|(\w*Impl\d*)|(\w*Implementation))\s+struct",
        "include": r"\.go$",
        "exclude": r"vendor/",
        "message": "禁止使用无意义命名如 DefaultPacket、PacketImpl，请使用语义化命名如 JsonPacket",
        "severity": "WARN",
    },
    {
        "id": "RECEIVER_NAMING",
        "pattern": r"func\s*\(\s*(\w+)\s+\*?\w+\s*\)",
        "include": r"\.go$",
        "exclude": r"vendor/|_test\.go$",
        "message": "建议 receiver 变量名使用小写 t",
        "severity": "WARN",
    },
]


def is_in_comment(line: str, pos: int) -> bool:
    before = line[:pos]
    stripped = before.lstrip()
    if stripped.startswith("//"):
        return True
    return False


def is_in_string(line: str, pos: int) -> bool:
    count = 0
    for i, ch in enumerate(line[:pos]):
        if ch == '"' and (i == 0 or line[i - 1] != '\\'):
            count += 1
    return count % 2 == 1


def check_file(filepath: str, check: Dict[str, Any], project_path: str) -> List[Dict[str, Any]]:
    results = []
    filename = os.path.basename(filepath)

    if check.get("match_filename"):
        if re.search(check["pattern"], filename):
            rel_path = os.path.relpath(filepath, project_path)
            results.append({
                "level": "L2",
                "severity": check["severity"],
                "file": rel_path,
                "line": "",
                "check": check["id"],
                "message": check["message"],
            })
        return results

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except (IOError, OSError):
        return results

    for line_num, line in enumerate(lines, 1):
        for match in re.finditer(check["pattern"], line):
            pos = match.start()
            if is_in_comment(line, pos) or is_in_string(line, pos):
                continue
            if check["id"] == "RECEIVER_NAMING":
                var_name = match.group(1)
                if var_name == "t":
                    continue
                if len(var_name) == 1 and var_name.islower():
                    continue
            rel_path = os.path.relpath(filepath, project_path)
            results.append({
                "level": "L2",
                "severity": check["severity"],
                "file": rel_path,
                "line": str(line_num),
                "check": check["id"],
                "message": check["message"],
            })
    return results


def run(project_path: str) -> List[Dict[str, Any]]:
    results = []
    exclude_dirs = {"vendor", ".git", "node_modules", "bin", "dist"}

    for check in CHECKS:
        include_re = re.compile(check["include"])
        exclude_re = re.compile(check["exclude"]) if check.get("exclude") else None

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for filename in files:
                filepath = os.path.join(root, filename)
                if not include_re.search(filename):
                    continue
                if exclude_re and exclude_re.search(filepath.replace("\\", "/")):
                    continue
                results.extend(check_file(filepath, check, project_path))

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python l2_standards.py <project_path>")
        sys.exit(1)
    results = run(sys.argv[1])
    for r in results:
        print(f"[{r['level']}][{r['severity']}] {r['check']}: {r['file']}:{r['line']} - {r['message']}")