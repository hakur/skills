"""L2 Code Duplication Detection - Using dupl tool"""
import subprocess
import sys
import os
import re
from typing import List, Dict, Any


def parse_dupl_output(output: str, project_path: str) -> List[Dict[str, Any]]:
    """Parse dupl output and convert to standard format.
    
    dupl output format:
    found N clones:
      file1.go:10,20
      file2.go:15,25
    """
    results = []
    lines = output.strip().split("\n")
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Match "found N clones:" header
        match = re.match(r"found (\d+) clones:", line)
        if match:
            clone_count = int(match.group(1))
            locations = []
            i += 1
            
            # Collect all locations for this clone group
            while i < len(lines) and lines[i].strip().startswith("  "):
                loc_line = lines[i].strip()
                # Parse "file.go:start,end" format
                loc_match = re.match(r"(.+):(\d+),(\d+)", loc_line)
                if loc_match:
                    file_path = loc_match.group(1)
                    start_line = loc_match.group(2)
                    end_line = loc_match.group(3)
                    rel_path = os.path.relpath(os.path.join(project_path, file_path), project_path)
                    locations.append({
                        "file": rel_path,
                        "start": start_line,
                        "end": end_line,
                    })
                i += 1
            
            # Determine severity based on clone count
            # dupl reports pairs, so 2 locations = 1 duplicate
            # 2 occurrences (1 duplicate) = WARN
            # 3+ occurrences (2+ duplicates) = ERROR
            if len(locations) >= 3:
                severity = "ERROR"
                message = f"代码重复 {len(locations)} 处，必须重构提取公共函数"
            else:
                severity = "WARN"
                message = f"代码重复 {len(locations)} 处，建议提取公共函数"
            
            # Create a result for each location
            for loc in locations:
                results.append({
                    "level": "L2",
                    "severity": severity,
                    "file": loc["file"],
                    "line": loc["start"],
                    "check": "CODE_DUPLICATION",
                    "message": f"{message} (行 {loc['start']}-{loc['end']})",
                })
        else:
            i += 1
    
    return results


def run(project_path: str) -> List[Dict[str, Any]]:
    """Run dupl to detect code duplication."""
    results = []
    
    # Get threshold from environment variable, default 15
    threshold = os.environ.get("DUPL_THRESHOLD", "15")
    
    try:
        # Run dupl command
        result = subprocess.run(
            ["dupl", "-t", threshold, "./..."],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        # dupl exits with code 0 even when duplicates found
        # We parse stdout for results
        if result.stdout:
            results = parse_dupl_output(result.stdout, project_path)
            
    except FileNotFoundError:
        results.append({
            "level": "L2",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "dupl",
            "message": "dupl 工具未安装，跳过代码重复检查。安装: go install github.com/mibk/dupl@latest",
        })
    except subprocess.TimeoutExpired:
        results.append({
            "level": "L2",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "dupl",
            "message": "dupl 检查超时",
        })
    except Exception as e:
        results.append({
            "level": "L2",
            "severity": "WARN",
            "file": "",
            "line": "",
            "check": "dupl",
            "message": f"dupl 检查出错: {e}",
        })
    
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python l2_dupl.py <project_path>")
        sys.exit(1)
    results = run(sys.argv[1])
    for r in results:
        print(f"[{r['level']}][{r['severity']}] {r['check']}: {r['file']}:{r['line']} - {r['message']}")
