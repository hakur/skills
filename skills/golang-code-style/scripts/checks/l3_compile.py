"""L3 Compile and Test Verification - go build + go test"""
import subprocess
import sys
from typing import List, Dict, Any


def run_go_build(project_path: str) -> List[Dict[str, Any]]:
    errors = []
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            for line in result.stderr.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split(":", 3)
                if len(parts) >= 3:
                    errors.append({
                        "level": "L3",
                        "severity": "ERROR",
                        "file": parts[0],
                        "line": parts[1] if len(parts) > 1 else "",
                        "check": "go-build",
                        "message": parts[-1].strip() if parts else line.strip(),
                    })
                else:
                    errors.append({
                        "level": "L3",
                        "severity": "ERROR",
                        "file": "",
                        "line": "",
                        "check": "go-build",
                        "message": line.strip(),
                    })
    except FileNotFoundError:
        errors.append({
            "level": "L3",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "go-build",
            "message": "go command not found, skipping go build",
        })
    except subprocess.TimeoutExpired:
        errors.append({
            "level": "L3",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "go-build",
            "message": "go build timed out",
        })
    return errors


def run_go_test(project_path: str) -> List[Dict[str, Any]]:
    errors = []
    try:
        result = subprocess.run(
            ["go", "test", "./..."],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            for line in (result.stderr + result.stdout).strip().split("\n"):
                if not line.strip():
                    continue
                if "FAIL" in line or "--- FAIL" in line:
                    errors.append({
                        "level": "L3",
                        "severity": "ERROR",
                        "file": "",
                        "line": "",
                        "check": "go-test",
                        "message": line.strip(),
                    })
    except FileNotFoundError:
        errors.append({
            "level": "L3",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "go-test",
            "message": "go command not found, skipping go test",
        })
    except subprocess.TimeoutExpired:
        errors.append({
            "level": "L3",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "go-test",
            "message": "go test timed out",
        })
    return errors


def run(project_path: str) -> List[Dict[str, Any]]:
    results = []
    results.extend(run_go_build(project_path))
    results.extend(run_go_test(project_path))
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python l3_compile.py <project_path>")
        sys.exit(1)
    results = run(sys.argv[1])
    for r in results:
        print(f"[{r['level']}][{r['severity']}] {r['file']}:{r['line']} - {r['message']}")