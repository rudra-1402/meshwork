import ast
import json
import re
from pathlib import Path

from app import create_app

SUCCESS_CODES = {200, 201, 202, 204}
FAILURE_CODES = {400, 401, 403, 404, 405, 409, 422, 429, 500}


def normalize_route_to_regex(route: str) -> re.Pattern:
    # Convert Flask vars: /api/events/<int:event_id>/submit -> /api/events/[^/]+/submit
    pattern = re.sub(r"<[^>]+>", r"[^/]+", route)
    return re.compile(r"^" + pattern + r"$")


def get_routes():
    app = create_app()
    routes = []
    with app.app_context():
        for rule in app.url_map.iter_rules():
            if rule.endpoint == "static":
                continue
            methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
            routes.append(
                {
                    "endpoint": rule.endpoint,
                    "route": str(rule.rule),
                    "methods": methods,
                }
            )
    routes.sort(key=lambda r: (r["route"], ",".join(r["methods"])))
    return routes


def extract_test_info(test_file: Path):
    source = test_file.read_text(encoding="utf-8")
    tree = ast.parse(source)
    infos = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            text = ast.get_source_segment(source, node) or ""

            strings = []
            for n in ast.walk(node):
                if isinstance(n, ast.Constant) and isinstance(n.value, str):
                    strings.append(n.value)

            # Gather asserted status codes in this test function
            status_codes = set(int(code) for code in re.findall(r"status_code\s*==\s*(\d{3})", text))

            infos.append(
                {
                    "file": str(test_file).replace("\\", "/"),
                    "test_name": node.name,
                    "strings": strings,
                    "status_codes": sorted(status_codes),
                }
            )

    return infos


def collect_tests(test_root: Path):
    all_infos = []
    for path in sorted(test_root.glob("test_*.py")):
        all_infos.extend(extract_test_info(path))
    return all_infos


def route_coverage(routes, tests):
    results = []

    for route in routes:
        route_regex = normalize_route_to_regex(route["route"])

        matched_tests = []
        success = False
        failure = False

        for test in tests:
            matched = any(route_regex.match(s) for s in test["strings"] if s.startswith("/"))
            if not matched:
                continue

            matched_tests.append(
                {
                    "file": test["file"],
                    "test_name": test["test_name"],
                    "status_codes": test["status_codes"],
                }
            )

            codes = set(test["status_codes"])
            if codes & SUCCESS_CODES:
                success = True
            if codes & FAILURE_CODES:
                failure = True

        results.append(
            {
                **route,
                "tests": matched_tests,
                "has_success_case": success,
                "has_failure_case": failure,
                "covered": bool(matched_tests),
            }
        )

    return results


def main():
    repo_root = Path(__file__).resolve().parent
    test_root = repo_root / "tests"

    routes = get_routes()
    tests = collect_tests(test_root)
    coverage = route_coverage(routes, tests)

    uncovered = [r for r in coverage if not r["covered"]]
    missing_success = [r for r in coverage if r["covered"] and not r["has_success_case"]]
    missing_failure = [r for r in coverage if r["covered"] and not r["has_failure_case"]]

    summary = {
        "total_routes": len(coverage),
        "covered_routes": len([r for r in coverage if r["covered"]]),
        "uncovered_routes": len(uncovered),
        "covered_missing_success": len(missing_success),
        "covered_missing_failure": len(missing_failure),
    }

    out_json = {
        "summary": summary,
        "coverage": coverage,
        "uncovered_routes": uncovered,
        "missing_success_routes": missing_success,
        "missing_failure_routes": missing_failure,
    }

    output_json_path = repo_root / "route_test_coverage_report.json"
    output_json_path.write_text(json.dumps(out_json, indent=2), encoding="utf-8")

    checklist_lines = []
    checklist_lines.append("# Backend Route Test Coverage Checklist")
    checklist_lines.append("")
    checklist_lines.append("## Summary")
    checklist_lines.append("")
    checklist_lines.append(f"- Total routes: {summary['total_routes']}")
    checklist_lines.append(f"- Covered routes: {summary['covered_routes']}")
    checklist_lines.append(f"- Uncovered routes: {summary['uncovered_routes']}")
    checklist_lines.append(f"- Covered but missing success-case assertion: {summary['covered_missing_success']}")
    checklist_lines.append(f"- Covered but missing failure-case assertion: {summary['covered_missing_failure']}")
    checklist_lines.append("")

    checklist_lines.append("## Uncovered Routes")
    checklist_lines.append("")
    if uncovered:
        for r in uncovered:
            methods = ",".join(r["methods"])
            checklist_lines.append(f"- [ ] `{methods} {r['route']}` ({r['endpoint']})")
    else:
        checklist_lines.append("- [x] None")
    checklist_lines.append("")

    checklist_lines.append("## Covered Routes Missing Success Case")
    checklist_lines.append("")
    if missing_success:
        for r in missing_success:
            methods = ",".join(r["methods"])
            checklist_lines.append(f"- [ ] `{methods} {r['route']}` ({r['endpoint']})")
    else:
        checklist_lines.append("- [x] None")
    checklist_lines.append("")

    checklist_lines.append("## Covered Routes Missing Failure Case")
    checklist_lines.append("")
    if missing_failure:
        for r in missing_failure:
            methods = ",".join(r["methods"])
            checklist_lines.append(f"- [ ] `{methods} {r['route']}` ({r['endpoint']})")
    else:
        checklist_lines.append("- [x] None")
    checklist_lines.append("")

    output_md_path = repo_root / "ROUTE_TEST_COVERAGE_CHECKLIST.md"
    output_md_path.write_text("\n".join(checklist_lines), encoding="utf-8")

    print(json.dumps(summary))
    print(f"JSON report: {output_json_path}")
    print(f"Checklist: {output_md_path}")


if __name__ == "__main__":
    main()
