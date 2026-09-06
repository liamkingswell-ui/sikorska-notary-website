#!/usr/bin/env python3
"""Change the practice's details safely across every page.

There is no build step and no template, so the header, footer and calls to
action are copied into all eleven pages. The phone number alone appears in more
than sixty places, in three different formats: the tel: link, the version people
read, and the structured data Google uses. Changing it by hand will miss some,
and a half-changed phone number on a notary's website means lost enquiries.

Run with no arguments to see what is currently set and where.

    python update-details.py                       show current values and counts
    python update-details.py --bump-version        make a CSS or JS edit take effect
    python update-details.py --phone "07123 456789"
    python update-details.py --email new@example.com

Nothing is written unless you add --apply. Without it you get a preview.

    python update-details.py --phone "07123 456789" --apply
"""
import argparse, datetime, glob, io, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES = sorted(glob.glob(os.path.join(ROOT, "*.html")))

CURRENT = {
    "phone_display": "07401 388 094",
    "phone_intl":    "+447401388094",
    "email":         "office@sikorskanotary.co.uk",
}


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def normalise_phone(raw):
    """Accept '07123 456789', '+44 7123 456789' or '07123456789'.

    Returns (display, international). A UK mobile entered in 07 form becomes
    +447... for the tel: link and the structured data, because that is what
    dialling from abroad needs.
    """
    digits = re.sub(r"[^\d+]", "", raw)
    if digits.startswith("+44"):
        national = "0" + digits[3:]
        intl = digits
    elif digits.startswith("0"):
        national = digits
        intl = "+44" + digits[1:]
    else:
        sys.exit("Could not read '%s' as a UK number. Use 07123 456789 or +44 7123 456789." % raw)
    if len(national) != 11:
        sys.exit("'%s' gives %d digits, expected 11 for a UK number." % (raw, len(national)))
    display = raw.strip() if " " in raw.strip() else "%s %s %s" % (national[:5], national[5:8], national[8:])
    return display, intl


def report():
    print("Current details, and how many places each appears:\n")
    checks = [
        ("Phone, as displayed", CURRENT["phone_display"]),
        ("Phone, tel: links",   "tel:" + CURRENT["phone_intl"]),
        ("Phone, structured data", '"' + CURRENT["phone_intl"] + '"'),
        ("Email",               CURRENT["email"]),
    ]
    for label, needle in checks:
        total = sum(read(p).count(needle) for p in PAGES)
        files = sum(1 for p in PAGES if needle in read(p))
        print("  %-24s %-32s %3d places in %2d files" % (label, needle, total, files))

    vers = set()
    for p in PAGES:
        vers |= set(re.findall(r"site\.(?:css|js)\?v=(\d+)", read(p)))
    print("\n  Asset version%s: %s" % ("s" if len(vers) > 1 else "", ", ".join(sorted(vers)) or "none"))
    if len(vers) > 1:
        print("  WARNING: the version is not the same everywhere. Run --bump-version to fix it.")
    print("\n  %d pages checked." % len(PAGES))


def apply_change(pairs, apply, what):
    """pairs is a list of (old, new). Reports per file, writes only if apply."""
    touched, total = 0, 0
    for p in PAGES:
        s = orig = read(p)
        hits = 0
        for old, new in pairs:
            hits += s.count(old)
            s = s.replace(old, new)
        if s != orig:
            touched += 1
            total += hits
            print("  %-34s %3d change%s" % (os.path.basename(p), hits, "" if hits == 1 else "s"))
            if apply:
                write(p, s)
    if not touched:
        print("  Nothing to change. The value may already be set.")
        return
    print("\n  %s: %d changes across %d files." % (what, total, touched))
    print("  WRITTEN." if apply else "  Preview only. Add --apply to write these.")


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phone", help="New phone number, e.g. \"07123 456789\"")
    ap.add_argument("--email", help="New email address")
    ap.add_argument("--bump-version", action="store_true",
                    help="Set the CSS and JS version to today. Do this after editing site.css or site.js.")
    ap.add_argument("--apply", action="store_true", help="Actually write the changes")
    a = ap.parse_args()

    if not PAGES:
        sys.exit("No .html files found. Run this from inside the website folder.")

    if not (a.phone or a.email or a.bump_version):
        report()
        print("\nNothing changed. See --help for what this can do.")
        return

    if a.phone:
        disp, intl = normalise_phone(a.phone)
        print("Phone -> %s (%s)\n" % (disp, intl))
        apply_change([
            ("tel:" + CURRENT["phone_intl"], "tel:" + intl),
            ('"' + CURRENT["phone_intl"] + '"', '"' + intl + '"'),
            (CURRENT["phone_display"], disp),
        ], a.apply, "Phone")
        print()

    if a.email:
        if "@" not in a.email:
            sys.exit("'%s' does not look like an email address." % a.email)
        print("Email -> %s\n" % a.email)
        apply_change([(CURRENT["email"], a.email)], a.apply, "Email")
        print()

    if a.bump_version:
        today = datetime.date.today().strftime("%Y%m%d")
        print("Asset version -> %s\n" % today)
        touched = 0
        for p in PAGES:
            s = orig = read(p)
            s = re.sub(r"site\.css\?v=\d+", "site.css?v=" + today, s)
            s = re.sub(r"site\.js\?v=\d+", "site.js?v=" + today, s)
            if s != orig:
                touched += 1
                print("  %s" % os.path.basename(p))
                if a.apply:
                    write(p, s)
        if not touched:
            print("  Already at %s everywhere." % today)
        else:
            print("\n  %d files." % touched)
            print("  WRITTEN. Re-upload the HTML files." if a.apply
                  else "  Preview only. Add --apply to write these.")

    if not a.apply:
        print("\nNothing was written. Re-run the same command with --apply.")


if __name__ == "__main__":
    main()
