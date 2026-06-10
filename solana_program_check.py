#!/usr/bin/env python3
"""
Heuristic security checklist for Solana program source. NOT an audit.

Scans Rust program source for the presence (or worrying absence) of the common
standing defenses, and flags smells worth a human -- or an agent -- reviewing.
Comments and the bodies of // line-comments are stripped before scanning, so a
comment that merely *mentions* a defense is never miscounted as the defense
being present. It is still regex-based and deliberately simple: expect false
positives and false negatives. A first-pass checklist, not a proof.

Usage:
    python solana_program_check.py <path-to-program-src-dir-or-file>

Exit code is non-zero only if a CORE defense (signer / owner / PDA re-derivation)
is entirely absent, so it is safe to drop into CI as an early-warning tripwire.
"""
import re, sys
from pathlib import Path


def collect_rs(target: Path):
    if target.is_file():
        return [target] if target.suffix == ".rs" else []
    return sorted(target.rglob("*.rs"))


def find_cargo(target: Path):
    here = target if target.is_dir() else target.parent
    for d in [here, *here.parents]:
        if (d / "Cargo.toml").exists():
            return d / "Cargo.toml"
    return None


def prep(text: str):
    """Return (orig_lines, scan_lines). scan_lines have comments removed so we
    never match a defense that only appears in a comment. Line numbers align."""
    def blank_block(m):
        return "\n" * m.group(0).count("\n")  # preserve newline count
    no_block = re.sub(r"/\*.*?\*/", blank_block, text, flags=re.DOTALL)
    orig = text.splitlines()
    scan = []
    for line in no_block.splitlines():
        i = line.find("//")
        scan.append(line[:i] if i >= 0 else line)
    return orig, scan


def main():
    if len(sys.argv) < 2:
        print("usage: python solana_program_check.py <src-dir-or-file>")
        sys.exit(2)

    target = Path(sys.argv[1])
    rs_files = collect_rs(target)
    if not rs_files:
        print("no .rs files found at", target)
        sys.exit(2)

    sources = []  # (name, orig_lines, scan_lines)
    for f in rs_files:
        orig, scan = prep(f.read_text(encoding="utf-8", errors="replace"))
        sources.append((f.name, orig, scan))

    def hits(pattern):
        out = []
        for name, orig, scan in sources:
            for i, sline in enumerate(scan):
                if re.search(pattern, sline):
                    disp = orig[i] if i < len(orig) else sline
                    out.append((name, i + 1, disp.strip()))
        return out

    def count(pattern):
        return len(hits(pattern))

    print("=" * 66)
    print("Solana program heuristic security check  (NOT an audit)")
    print(f"Target: {target}  |  {len(rs_files)} .rs file(s)")
    print("=" * 66)

    print("\n[ build profile ]")
    cargo = find_cargo(target)
    if cargo is None:
        print("  ?       Cargo.toml not found near target")
    elif re.search(r"overflow-checks\s*=\s*true", cargo.read_text(encoding="utf-8", errors="replace")):
        print("  OK      overflow-checks = true")
    else:
        print("  REVIEW  overflow-checks not set to true -> arithmetic can wrap silently in release")

    print("\n[ standing defenses present ]")
    core_missing = False
    defenses = [
        ("signer checks",          r"is_signer",                                   True),
        ("owner checks",           r"\.owner\(\)",                                 True),
        ("PDA re-derivation",      r"find_program_address|create_program_address", True),
        ("checked token transfer", r"[Tt]ransfer[Cc]hecked|transfer_checked",      False),
        ("checked arithmetic",     r"checked_(add|sub|mul|div)",                   False),
        ("account close / zero",   r"set_lamports\s*\(\s*0|\.fill\(0\)|close\(",   False),
    ]
    for name, pat, is_core in defenses:
        n = count(pat)
        if n > 0:
            print(f"  OK      {name:<24} {n}")
        else:
            print(f"  REVIEW  {name:<24} 0   <- not found; confirm this is intentional")
            if is_core:
                core_missing = True

    print("\n[ smells to review ]")
    any_smell = False

    raw_tx = [h for h in hits(r"\bTransfer\s*\{|::transfer\s*\(") if "checked" not in h[2].lower()]
    if raw_tx:
        any_smell = True
        print(f"  raw transfer x{len(raw_tx)}  (fine for SOL; for SPL tokens prefer *_checked):")
        for name, ln, s in raw_tx[:8]:
            print(f"      {name}:{ln}  {s[:78]}")

    panics = hits(r"\.unwrap\(\)|\.expect\(|panic!\(")
    if panics:
        any_smell = True
        print(f"  panic-on-error x{len(panics)}  (.unwrap/.expect/panic! -- many benign, but each can abort):")
        for name, ln, s in panics[:8]:
            print(f"      {name}:{ln}  {s[:78]}")

    status_flag = hits(r"\.?status\s*=[^=]")
    if status_flag:
        any_smell = True
        print(f"  status-flag write x{len(status_flag)}  (finalize by CLOSING the account, not only flipping a flag):")
        for name, ln, s in status_flag[:6]:
            print(f"      {name}:{ln}  {s[:78]}")

    if not any_smell:
        print("  none of the heuristic smells matched")

    print("\n" + "-" * 66)
    print("Heuristic checklist aid, NOT a security audit. False positives and")
    print("false negatives are expected. Get a real review before mainnet.")
    sys.exit(1 if core_missing else 0)


if __name__ == "__main__":
    main()
