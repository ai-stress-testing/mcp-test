#!/usr/bin/env python3
"""Generate agents/INDEX.md from agent.md frontmatter, with roster lint.

Run from the repo root: python3 scripts/build_index.py
Fails (exit 1) on lint violations so CI can gate on it later.
"""
import glob
import json
import re
import sys
import tomllib

ROOT = "agents"
OUT = f"{ROOT}/INDEX.md"
# ponytail: naive frontmatter split, swap for a YAML parser if fields grow
FM = re.compile(r"^---\n(.*?)\n---", re.S)
# Backticked `team/role`-shaped handoff mentions, e.g. `pm/project-manager`.
HANDOFF_RE = re.compile(r"`([a-z][a-z0-9-]*)/([a-z0-9-]+)`")
MUTATION_TOOLS = {"Edit", "Bash", "NotebookEdit"}  # forbidden for opus, no exceptions
# Write is also forbidden for opus, except roles listed here with a reason.
OPUS_WRITE_EXCEPTIONS = {
    "agents/pm/project-manager/agent.md":
        "spec-driven PM: Write is docs/-scoped (specs, backlog, PRD drafts), never code",
}

# GT-33: model sovereignty. Frontmatter `model:` may be a concrete model id
# (unchanged, existing behavior) or a capability tier from MODELS_TOML,
# resolved here for lint/display. See docs/model-tiers.md.
MODELS_TOML = "scripts/models.toml"

# GT-13 / threat-model C6: tool-set widening lint. Baseline snapshot of each
# role's tools as of the last intentional refresh; a role's current tools
# strictly widening that snapshot is a lint problem. Refresh intentionally
# with `python3 scripts/build_index.py --update-tools-baseline`.
TOOLS_BASELINE = "scripts/tools-baseline.json"


def load_model_config(path=MODELS_TOML):
    """Load ({tier: id}, {alias: id}) from models.toml. Missing file ->
    empty maps (every `model:` value must then be a concrete id already)."""
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return {}, {}
    return data.get("tiers", {}), data.get("aliases", {})


def resolve_model(raw, tiers, aliases, concrete_models):
    """Resolve a frontmatter `model:` value to (resolved_id, tier_used).
    A tier name resolves via [tiers] (tier_used set); an alias via
    [aliases]; a concrete id is used as-is (tier_used None). Returns
    (None, None) if `raw` is none of these — a lint problem."""
    if raw in concrete_models:
        return raw, None
    if raw in tiers:
        return tiers[raw], raw
    if raw in aliases:
        return aliases[raw], None
    return None, None


def load_tools_baseline(path=TOOLS_BASELINE):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def collect_role_tools():
    """{"team/role": sorted [tools]} for every current role. Shared by the
    baseline-refresh routine and (indirectly, via parse()) the lint."""
    baseline = {}
    for path in sorted(glob.glob(f"{ROOT}/*/*/agent.md")):
        _, team, role, _ = path.split("/")
        if team == "TEMPLATE":
            continue
        fm = parse(path)
        tools = sorted({t.strip() for t in fm.get("tools", "").split(",") if t.strip()})
        baseline[f"{team}/{role}"] = tools
    return baseline


def update_tools_baseline():
    """Intentional refresh: `python3 scripts/build_index.py --update-tools-baseline`.
    Snapshots the CURRENT roster's tools as the new baseline — use this
    after a reviewed, deliberate tool grant, not to silence the lint."""
    baseline = collect_role_tools()
    with open(TOOLS_BASELINE, "w") as f:
        json.dump(baseline, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"wrote {TOOLS_BASELINE}: {len(baseline)} roles")
    return 0


def parse(path):
    text = open(path).read()
    m = FM.match(text)
    fm = {}
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    return fm


def check_handoff_references(team_names, roles):
    """Scan agent.md/SPEC.md/team-README files for backticked `team/role`
    mentions and flag any that don't resolve to a real role. `README` as
    the second segment (e.g. `pm/README`) is a file reference, not a
    handoff, and is never flagged."""
    problems = []
    paths = sorted(
        glob.glob(f"{ROOT}/*/*/agent.md")
        + glob.glob(f"{ROOT}/*/*/SPEC.md")
        + glob.glob(f"{ROOT}/*/README.md")
    )
    for path in paths:
        text = open(path).read()
        for team, ref in HANDOFF_RE.findall(text):
            if team not in team_names or ref == "README":
                continue
            if f"{team}/{ref}" not in roles:
                problems.append(f"{path}: broken handoff reference `{team}/{ref}`")
    return problems


def main():
    if "--update-tools-baseline" in sys.argv[1:]:
        return update_tools_baseline()

    problems = []
    teams = {}
    models = {}
    tiers, aliases = load_model_config()
    concrete_models = set(tiers.values()) | set(aliases.values())
    reason_model = tiers.get("reason")  # the read-only tier, whatever its id
    short_name = {v: k for k, v in aliases.items()}  # id -> readable label
    tools_baseline = load_tools_baseline()
    team_names = {
        p.rstrip("/").split("/")[-1]
        for p in glob.glob(f"{ROOT}/*/")
        if p.rstrip("/").split("/")[-1] != "TEMPLATE"
    }
    roles = set()
    for path in sorted(glob.glob(f"{ROOT}/*/*/agent.md")):
        _, team, role, _ = path.split("/")
        if team == "TEMPLATE":
            continue
        roles.add(f"{team}/{role}")
        fm = parse(path)
        for field in ("name", "description", "tools", "model"):
            if not fm.get(field):
                problems.append(f"{path}: missing frontmatter field '{field}'")
        spec = path.replace("agent.md", "SPEC.md")
        if not glob.glob(spec):
            problems.append(f"{path}: missing SPEC.md sibling")
        tools = {t.strip() for t in fm.get("tools", "").split(",")}

        # GT-33: `model:` is either a concrete model (unchanged) or a tier
        # from models.toml, resolved here for lint + display.
        raw_model = fm.get("model", "")
        resolved_model, tier_used = (None, None)
        if raw_model:
            resolved_model, tier_used = resolve_model(
                raw_model, tiers, aliases, concrete_models
            )
            if resolved_model is None:
                problems.append(
                    f"{path}: unknown model '{raw_model}' — not a known id"
                    f" ({sorted(concrete_models)}), tier ({sorted(tiers)}),"
                    f" or alias ({sorted(aliases)})"
                )

        if reason_model and resolved_model == reason_model:
            bad = tools & MUTATION_TOOLS
            if "Write" in tools and path not in OPUS_WRITE_EXCEPTIONS:
                bad = bad | {"Write"}
            if bad:
                problems.append(
                    f"{path}: reason-tier model paired with write tools {sorted(bad)}"
                    " — reasoning depth, not blast radius"
                )

        # GT-13 / threat-model C6: flag tool-set widening vs the committed
        # baseline. A role missing from the baseline (new role since the
        # last refresh) is not flagged — there's nothing to compare against
        # yet. Tools removed or unchanged never trigger this.
        key = f"{team}/{role}"
        baseline_tools = tools_baseline.get(key)
        if baseline_tools is not None:
            baseline_set = set(baseline_tools)
            if tools > baseline_set:
                added = sorted(tools - baseline_set)
                problems.append(
                    f"{path}: tool-set widening vs baseline (added {added})"
                    " — needs security review; update baseline intentionally via"
                    " `python3 scripts/build_index.py --update-tools-baseline`"
                )

        # Display/count by a readable label (opus/sonnet/haiku/fable), while
        # models.toml holds the real ids — the id churns on a model bump, the
        # roster's labels don't.
        label = (
            short_name.get(resolved_model, resolved_model)
            if resolved_model
            else (raw_model or "?")
        )
        models[label] = models.get(label, 0) + 1
        model_display = f"{label} ({tier_used})" if tier_used else label

        one_liner = re.split(r"(?<=[.!?]) ", fm.get("description", ""))[0]
        teams.setdefault(team, []).append(
            (role, model_display, fm.get("tools", "?"), one_liner)
        )

    total = sum(len(v) for v in teams.values())
    model_summary = ", ".join(f"{k}: {v}" for k, v in sorted(models.items()))

    lines = [
        "# Agent Index",
        "",
        "Generated by `scripts/build_index.py` — do not edit by hand.",
        "",
        f"**{total} agents** across **{len(teams)} teams**. Models — {model_summary}.",
        "",
    ]
    for team in sorted(teams):
        lines.append(f"## {team} ({len(teams[team])})")
        lines.append("")
        lines.append("| Role | Model | Tools | What it does |")
        lines.append("|---|---|---|---|")
        for role, model, tools, desc in teams[team]:
            lines.append(f"| [{role}]({team}/{role}/) | {model} | {tools} | {desc} |")
        lines.append("")

    open(OUT, "w").write("\n".join(lines))
    print(f"wrote {OUT}: {total} agents, {len(teams)} teams ({model_summary})")

    problems.extend(check_handoff_references(team_names, roles))

    if problems:
        print(f"\n{len(problems)} lint problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
