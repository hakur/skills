"""L2 Ruleguard AST Check - Using golangci-lint with ruleguard"""
import subprocess
import sys
import os
from typing import List, Dict, Any


def parse_golangci_lint_output(output: str, project_path: str) -> List[Dict[str, Any]]:
    """Parse golangci-lint output with ruleguard findings.
    
    Expected format:
    file.go:10:5: ruleguard: message (ruleguard-check)
    """
    results = []
    
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line or not ":" in line:
            continue
        
        # Parse "file.go:10:5: ruleguard: message" format
        # or "file.go:10: ruleguard: message" format
        parts = line.split(":", 3)
        if len(parts) < 3:
            continue
        
        file_path = parts[0]
        line_num = parts[1]
        
        # Check if this is a ruleguard message
        remaining = ":".join(parts[2:])
        if "ruleguard" not in remaining:
            continue
        
        # Extract message
        message_match = remaining.split("ruleguard:", 1)
        if len(message_match) < 2:
            continue
        
        message = message_match[1].strip()
        
        # Determine severity based on message content
        # WARN-level messages typically contain "建议" or are naming conventions
        if any(keyword in message for keyword in ["建议", "命名", "规范"]):
            severity = "WARN"
        else:
            severity = "ERROR"
        
        results.append({
            "level": "L2",
            "severity": severity,
            "file": file_path,
            "line": line_num,
            "check": "ruleguard",
            "message": message,
        })
    
    return results


def run(project_path: str) -> List[Dict[str, Any]]:
    """Run ruleguard via golangci-lint."""
    results = []
    
    # Get the rule file path
    # The rule file is relative to the skill directory
    skill_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    rule_file = os.path.join(skill_dir, "references", "ruleguard", "rules.go")
    
    # Check if rule file exists
    if not os.path.exists(rule_file):
        results.append({
            "level": "L2",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "ruleguard",
            "message": f"ruleguard 规则文件不存在: {rule_file}",
        })
        return results
    
    try:
        # Create temporary golangci-lint config
        config_content = f"""linters:
  disable-all: true
  enable:
    - ruleguard

linters-settings:
  ruleguard:
    rules: "{rule_file}"
"""
        
        config_path = os.path.join(project_path, ".golangci.ruleguard.yml")
        with open(config_path, "w") as f:
            f.write(config_content)
        
        try:
            # Run golangci-lint with ruleguard
            result = subprocess.run(
                ["golangci-lint", "run", "--config", config_path, "./..."],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=180,
            )
            
            # Parse results
            if result.stdout:
                results = parse_golangci_lint_output(result.stdout, project_path)
            
            # If there are compilation errors in stderr, report them
            if result.returncode != 0 and result.stderr and "ruleguard" in result.stderr:
                results.append({
                    "level": "L2",
                    "severity": "WARN",
                    "file": "",
                    "line": "",
                    "check": "ruleguard",
                    "message": f"ruleguard 检查出错: {result.stderr[:200]}",
                })
        finally:
            # Clean up temporary config
            if os.path.exists(config_path):
                os.remove(config_path)
                
    except FileNotFoundError:
        results.append({
            "level": "L2",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "ruleguard",
            "message": "golangci-lint 未安装，跳过 ruleguard 检查。安装: https://golangci-lint.run/usage/install/",
        })
    except subprocess.TimeoutExpired:
        results.append({
            "level": "L2",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "ruleguard",
            "message": "ruleguard 检查超时",
        })
    except Exception as e:
        results.append({
            "level": "L2",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "ruleguard",
            "message": f"ruleguard 检查出错: {e}",
        })
    
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python l2_ruleguard.py <project_path>")
        sys.exit(1)
    results = run(sys.argv[1])
    for r in results:
        print(f"[{r['level']}][{r['severity']}] {r['check']}: {r['file']}:{r['line']} - {r['message']}")
