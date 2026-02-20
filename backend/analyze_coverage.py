import json
with open("coverage.json") as f:
    data = json.load(f)

files = data["files"]
rows = []
for path, info in files.items():
    name = path.replace("app\\", "").replace("app/", "")
    stmts = info["summary"]["num_statements"]
    missing = info["summary"]["missing_lines"]
    pct = int(info["summary"]["percent_covered_display"].replace("%",""))
    rows.append((pct, name, stmts, missing))

rows.sort()
print(f"\n{'PCT':>4}  {'STMTS':>5}  {'MISS':>5}  MODULE")
print("-" * 65)
for pct, name, stmts, missing in rows:
    flag = "  <-- ROUTES (HTML)" if "routes" in name and pct < 50 else ""
    print(f"{pct:3}%  {stmts:5}  {missing:5}  {name}{flag}")

total = data["totals"]
print()
print(f"TOTAL: {total['percent_covered_display']}  ({total['num_statements']} stmts, {total['missing_lines']} missing)")

# Calculate: what if every route was JSON-testable to 90%?
html_route_modules = [r for r in rows if "routes" in r[1] and r[0] < 50]
html_service_modules = [r for r in rows if "services" in r[1] and r[0] < 50]
currently_missing = total["missing_lines"]
currently_stmts = total["num_statements"]

print("\n--- POTENTIAL GAIN ANALYSIS ---")
print(f"Currently: {total['percent_covered_display']} ({currently_missing} lines uncovered)")
print()

# Lines that STAY hard to cover regardless (error handlers deep in code)
hard_to_cover_estimate = 50  # db errors, retries, etc

# If HTML routes got to 90% coverage
route_gain = 0
for pct, name, stmts, missing in html_route_modules:
    could_cover = int(stmts * 0.90) - (stmts - missing)
    route_gain += max(0, could_cover)
    print(f"  Route {name}: {pct}% -> 90% (~+{max(0,could_cover)} lines)")

print()
service_gain = 0
for pct, name, stmts, missing in html_service_modules:
    could_cover = int(stmts * 0.85) - (stmts - missing)
    service_gain += max(0, could_cover)
    print(f"  Service {name}: {pct}% -> 85% (~+{max(0,could_cover)} lines)")

total_gain = route_gain + service_gain
new_covered = (currently_stmts - currently_missing) + total_gain
new_missing = currently_missing - total_gain
new_pct = new_covered / currently_stmts * 100
print(f"\nProjected new total: ~{new_pct:.0f}%")
print(f"(+{total_gain} lines covered, {new_missing} still missing)")
print(f"\nTo hit 95%: need {int(currently_stmts * 0.95) - (currently_stmts - currently_missing)} more lines covered")
print(f"To hit 90%: need {int(currently_stmts * 0.90) - (currently_stmts - currently_missing)} more lines covered")
print(f"To hit 85%: need {int(currently_stmts * 0.85) - (currently_stmts - currently_missing)} more lines covered")
