#!/usr/bin/env bash
set -euo pipefail

# framer-deploy.sh
# Pulls a Framer site, strips Framer branding, and prepares it for GitHub Pages deployment.
#
# Usage:
#   ./scripts/framer-deploy.sh <framer-url> <output-dir> [--cname <domain>]
#
# Examples:
#   ./landing-page/framer-deploy.sh https://thankful-apartment-080430.framer.app/ ./docs
#   ./landing-page/framer-deploy.sh https://my-site.framer.app/ ./docs --cname archetype.dev
#
# What it strips (minimal, only Framer branding):
#   - The __framer-badge-container div (the "Made with Framer" badge)
#   - The editor bar script loader
# Everything else (scripts, fonts, styles, meta tags) is kept intact.

FRAMER_URL="${1:-}"
OUTPUT_DIR="${2:-}"
CNAME=""

if [[ -z "$FRAMER_URL" || -z "$OUTPUT_DIR" ]]; then
  echo "Usage: $0 <framer-url> <output-dir> [--cname <domain>]"
  exit 1
fi

# Parse optional flags
shift 2
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cname)
      CNAME="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

mkdir -p "$OUTPUT_DIR"

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

echo "Fetching $FRAMER_URL ..."
curl -sL "$FRAMER_URL" -o "$TMPFILE"

if [[ ! -s "$TMPFILE" ]]; then
  echo "Error: Failed to fetch HTML from $FRAMER_URL"
  exit 1
fi

echo "Cleaning Framer branding..."

python3 - "$TMPFILE" "$OUTPUT_DIR/index.html" "$FRAMER_URL" "$CNAME" << 'PYEOF'
import sys
import re

input_file = sys.argv[1]
output_file = sys.argv[2]
framer_url = sys.argv[3].rstrip("/")
cname = sys.argv[4] if len(sys.argv) > 4 else ""

with open(input_file, "r") as f:
    html = f.read()

original_size = len(html)

# 1. Remove the editor bar script loader in <head>
#    This is a <script> that checks localStorage for __framer_force_showing_editorbar_since
#    and injects a modulepreload link to framer.com/edit/init.mjs
html = re.sub(
    r'<script>try\{if\(localStorage\.get\("__framer_force_showing_editorbar_since"\)\).*?</script>\n?',
    '',
    html,
    flags=re.DOTALL
)

# 2. Remove the __framer-badge-container div by finding balanced div tags
#    Can't use a simple regex because the badge has nested divs, and scripts/links
#    come AFTER it in the body that we must keep.
marker = '<div id="__framer-badge-container">'
badge_start = html.find(marker)
if badge_start != -1:
    # Walk forward counting div depth to find the matching </div>
    i = badge_start
    depth = 0
    while i < len(html):
        if html[i:].startswith('<div'):
            depth += 1
            i = html.find('>', i) + 1
        elif html[i:].startswith('</div>'):
            depth -= 1
            i += 6  # len('</div>')
            if depth == 0:
                break
        else:
            i += 1
    # Also consume any HTML comments immediately after (<!--/$--> etc.)
    while i < len(html) and html[i:].startswith('<!--'):
        end_comment = html.find('-->', i)
        if end_comment == -1:
            break
        i = end_comment + 3
    badge_end = i
    # Remove the badge and any leading whitespace
    ws_start = badge_start
    while ws_start > 0 and html[ws_start - 1] in ' \t\n':
        ws_start -= 1
    html = html[:ws_start] + html[badge_end:]

# 3. Remove CSS rules targeting the badge container
html = re.sub(
    r'@supports\s*\(z-index:\s*calc\(infinity\)\)\s*\{#__framer-badge-container\{[^}]*\}\}',
    '',
    html
)
html = re.sub(
    r'#__framer-badge-container\{[^}]*\}',
    '',
    html
)

# 4. Replace Framer URL with custom domain if provided
if cname:
    custom_url = f"https://{cname}"
    html = html.replace(framer_url, custom_url)

with open(output_file, "w") as f:
    f.write(html)

final_size = len(html)
print(f"  Original: {original_size:,} bytes")
print(f"  Cleaned:  {final_size:,} bytes")
print(f"  Removed:  {original_size - final_size:,} bytes")
PYEOF

echo "Created $OUTPUT_DIR/index.html"

if [[ -n "$CNAME" ]]; then
  echo "$CNAME" > "$OUTPUT_DIR/CNAME"
  echo "Created $OUTPUT_DIR/CNAME (${CNAME})"
fi

touch "$OUTPUT_DIR/.nojekyll"
echo "Created $OUTPUT_DIR/.nojekyll"

# Verify
echo ""
if grep -q '__framer-badge-container' "$OUTPUT_DIR/index.html"; then
  echo "WARNING: Framer badge still present"
else
  echo "OK: Framer badge removed"
fi

if grep -q 'framer.com/edit' "$OUTPUT_DIR/index.html"; then
  echo "WARNING: Framer editor script still present"
else
  echo "OK: Framer editor script removed"
fi
