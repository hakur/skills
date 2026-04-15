"""L1 Static Analysis - go vet + golangci-lint"""
import subprocess
import sys
from typing import List, Dict, Any


def run_go_vet(project_path: str) -> List[Dict[str, Any]]:
    errors = []
    try:
        result = subprocess.run(
            ["go", "vet", "./..."],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            for line in result.stderr.strip().split("\n"):
                if line.strip():
                    parts = line.split(":", 3)
                    if len(parts) >= 3:
                        errors.append({
                            "level": "L1",
                            "severity": "ERROR",
                            "file": parts[0],
                            "line": parts[1] if len(parts) > 1 else "",
                            "check": "go-vet",
                            "message": parts[-1].strip() if parts else line.strip(),
                        })
                    else:
                        errors.append({
                            "level": "L1",
                            "severity": "ERROR",
                            "file": "",
                            "line": "",
                            "check": "go-vet",
                            "message": line.strip(),
                        })
    except FileNotFoundError:
        errors.append({
            "level": "L1",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "go-vet",
            "message": "go command not found, skipping go vet",
        })
    except subprocess.TimeoutExpired:
        errors.append({
            "level": "L1",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "go-vet",
            "message": "go vet timed out",
        })
    return errors


def run_golangci_lint(project_path: str) -> List[Dict[str, Any]]:
    errors = []
    try:
        result = subprocess.run(
            ["golangci-lint", "run", "./..."],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split(":", 3)
                if len(parts) >= 3:
                    errors.append({
                        "level": "L1",
                        "severity": "WARN",
                        "file": parts[0],
                        "line": parts[1] if len(parts) > 1 else "",
                        "check": "golangci-lint",
                        "message": parts[-1].strip() if parts else line.strip(),
                    })
    except FileNotFoundError:
        errors.append({
            "level": "L1",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "golangci-lint",
            "message": "golangci-lint not found, skipping",
        })
    except subprocess.TimeoutExpired:
        errors.append({
            "level": "L1",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "golangci-lint",
            "message": "golangci-lint timed out",
        })
    return errors


def run(project_path: str) -> List[Dict[str, Any]]:
    results = []
    results.extend(run_go_vet(project_path))
    results.extend(run_golangci_lint(project_path))
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python l1_static.py <project_path>")
        sys.exit(1)
    results = run(sys.argv[1])
    for r in results:
        print(f"[{r['level']}][{r['severity']}] {r['file']}:{r['line']} - {r['message']}")