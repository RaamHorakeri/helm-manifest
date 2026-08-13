#!/usr/bin/env python3
import subprocess
import json
import yaml
import argparse
from packaging.version import Version, InvalidVersion


def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p.stdout


def get_latest_chart_version(repo_name, chart_full_name):
    # helm search repo <repo>/<chart> --versions -o json
    out = run(["helm", "search", "repo", f"{repo_name}/{chart_full_name}", "--versions", "-o", "json"])
    arr = json.loads(out)
    versions = []
    for entry in arr:
        v = entry.get('version')
        if v:
            try:
                versions.append(Version(v))
            except InvalidVersion:
                # fallback to raw string
                versions.append(v)
    if not versions:
        raise RuntimeError(f"No versions found for {repo_name}/{chart_full_name}")
    # pick max
    try:
        vmax = str(max(versions))
    except TypeError:
        # mixed types, sort by string
        vmax = sorted(map(str, versions))[-1]
    return vmax


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chart-path', required=True)
    parser.add_argument('--repo-url', required=True)
    parser.add_argument('--chart-name', required=True)
    args = parser.parse_args()

    chart_path = args.chart_path
    repo_url = args.repo_url
    chart_name = args.chart_name

    # ensure helm repo
    try:
        run(["helm", "repo", "add", "argo", repo_url])
    except RuntimeError:
        # ignore if already exists
        pass
    run(["helm", "repo", "update"])

    # read Chart.yaml
    with open(chart_path, 'r', encoding='utf-8') as f:
        chart = yaml.safe_load(f)

    deps = chart.get('dependencies') or []
    dep = None
    for d in deps:
        if d.get('name') == chart_name:
            dep = d
            break
    if dep is None:
        raise RuntimeError(f"Dependency {chart_name} not found in {chart_path}")

    current_version = dep.get('version')
    latest_version = get_latest_chart_version('argo', chart_name)

    print(f"Current pinned: {current_version}")
    print(f"Latest available: {latest_version}")

    if str(latest_version) != str(current_version):
        print(f"Updating {chart_path}: {current_version} -> {latest_version}")
        dep['version'] = str(latest_version)
        # write back
        with open(chart_path, 'w', encoding='utf-8') as f:
            yaml.dump(chart, f, default_flow_style=False, sort_keys=False)
        # leave commit/PR to the workflow step
        print("UPDATED")
    else:
        print("UP-TO-DATE")


if __name__ == '__main__':
    main()
