"""Print the project tree, marking what git tracks, ignores, or hasn't seen yet.

  green  tracked       committed in the repo
  dim    ignored       matched by .gitignore or .git/info/exclude
  yellow untracked     new, not ignored, not yet committed

Ignored folders are shown but not opened (one line each, with a file count), so caches and
virtualenvs don't flood the view. Usage:  python3 design/scripts/tree.py [path] [--depth N]
"""
import os
import subprocess
import sys

GREEN, DIM, YELLOW, BOLD, RESET = "\033[32m", "\033[2m", "\033[33m", "\033[1m", "\033[0m"
SKIP = {".git"}
# Folders that are tracked but hold many generated files: show a count instead of every file.
COLLAPSE = {"docs/gallery/cards", "docs/gallery/cards/light"}


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, check=True).stdout


def load_status(root):
    tracked = set(git(root, "ls-files", "-z").split("\0")) - {""}
    tracked_dirs = {os.path.dirname(p) for p in tracked}
    for p in list(tracked_dirs):
        while p:
            p = os.path.dirname(p)
            tracked_dirs.add(p)
    ignored = set(git(root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--directory").split("\0")) - {""}
    ignored = {p.rstrip("/") for p in ignored}
    return tracked, tracked_dirs, ignored


def count_files(path):
    n = 0
    for _, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP]
        n += len(files)
    return n


def label(rel, is_dir, tracked, tracked_dirs, ignored):
    if rel in ignored or any(rel.startswith(i + "/") for i in ignored):
        return "ignored", DIM
    if (rel in tracked_dirs) if is_dir else (rel in tracked):
        return "tracked", GREEN
    return "untracked", YELLOW


def walk(root, rel, prefix, depth, max_depth, st, totals):
    path = os.path.join(root, rel)
    entries = sorted(os.listdir(path), key=lambda n: (not os.path.isdir(os.path.join(path, n)), n.lower()))
    entries = [e for e in entries if e not in SKIP]
    for i, name in enumerate(entries):
        last = i == len(entries) - 1
        child = os.path.join(rel, name) if rel else name
        full = os.path.join(root, child)
        is_dir = os.path.isdir(full)
        state, color = label(child, is_dir, *st)
        totals[state] += 1
        branch = "└── " if last else "├── "
        tag = f"{color}[{state}]{RESET}"
        if is_dir:
            n = count_files(full)
            folded = state == "ignored" or child in COLLAPSE or depth + 1 >= max_depth
            note = f"{DIM}  ({n} files){RESET}" if folded else ""
            print(f"{prefix}{branch}{color}{BOLD}{name}/{RESET}  {tag}{note}")
            if not folded:
                walk(root, child, prefix + ("    " if last else "│   "), depth + 1, max_depth, st, totals)
        else:
            print(f"{prefix}{branch}{color}{name}{RESET}  {tag}")


def main():
    args = sys.argv[1:]
    max_depth = 4
    if "--depth" in args:
        max_depth = int(args[args.index("--depth") + 1])
        del args[args.index("--depth"):args.index("--depth") + 2]
    root = os.path.abspath(args[0] if args else ".")
    branch = git(root, "branch", "--show-current").strip()
    print(f"{BOLD}{os.path.basename(root)}/{RESET}  {DIM}branch {branch}{RESET}")
    print(f"{GREEN}■ tracked{RESET}   {YELLOW}■ untracked{RESET}   {DIM}■ ignored (not opened){RESET}\n")
    totals = {"tracked": 0, "ignored": 0, "untracked": 0}
    walk(root, "", "", 0, max_depth, load_status(root), totals)
    print(f"\n{GREEN}{totals['tracked']} tracked{RESET} · {YELLOW}{totals['untracked']} untracked{RESET} · "
          f"{DIM}{totals['ignored']} ignored{RESET} entries shown")


if __name__ == "__main__":
    main()
