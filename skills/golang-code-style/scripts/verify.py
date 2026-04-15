"""Golang Code Style Verification - Main entry point

Runs L1 (static), L2 (standards), L3 (compile+test) checks in sequence.
"""
import sys
import os
import importlib.util
import io

# Fix encoding on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def load_checks_module(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def format_result(r: dict) -> str:
    parts = [f"[{r['level']}][{r['severity']}]"]
    if r.get('check'):
        parts.append(f"({r['check']})")
    if r.get('file'):
        loc = r['file']
        if r.get('line'):
            loc += f":{r['line']}"
        parts.append(loc + " -")
    parts.append(r['message'])
    return " ".join(parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify.py <project_path>")
        sys.exit(1)

    project_path = os.path.abspath(sys.argv[1])
    if not os.path.isdir(project_path):
        print(f"Error: {project_path} is not a directory")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    checks_dir = os.path.join(script_dir, "checks")

    all_results = []
    error_count = 0

    levels = [
        ("L1", "l1_static.py", "Static Analysis (go vet + golangci-lint)"),
        ("L2-dupl", "l2_dupl.py", "Code Duplication Detection"),
        ("L2-guard", "l2_ruleguard.py", "AST Rules Check (ruleguard)"),
        ("L3", "l3_compile.py", "Compile & Test Verification"),
    ]

    for level_name, module_file, description in levels:
        module_path = os.path.join(checks_dir, module_file)
        if not os.path.exists(module_path):
            print(f"  [!] {level_name}: {module_file} not found, skipping")
            continue

        print(f"\n{'='*60}")
        print(f"  {level_name}: {description}")
        print(f"{'='*60}")

        try:
            module = load_checks_module(f"checks.{module_file.replace('.py', '')}", module_path)
            results = module.run(project_path)
        except Exception as e:
            print(f"  Error running {module_file}: {e}")
            continue

        level_errors = 0
        for r in results:
            print(f"  {format_result(r)}")
            if r.get('severity') == 'ERROR':
                level_errors += 1
                error_count += 1

        if not results:
            print(f"  [OK] No issues found")
        elif level_errors == 0:
            print(f"\n  [!] {len(results)} warning(s)")
        else:
            print(f"\n  [X] {level_errors} error(s), {len(results) - level_errors} warning(s)")

        all_results.extend(results)

    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")

    error_count = sum(1 for r in all_results if r.get('severity') == 'ERROR')
    warn_count = sum(1 for r in all_results if r.get('severity') == 'WARN')

    if error_count == 0 and warn_count == 0:
        print("  [OK] All checks passed")
        sys.exit(0)
    elif error_count == 0:
        print(f"  [!] {warn_count} warning(s), 0 error(s)")
        sys.exit(0)
    else:
        print(f"  [X] {error_count} error(s), {warn_count} warning(s)")
        sys.exit(1)


if __name__ == "__main__":
    main()