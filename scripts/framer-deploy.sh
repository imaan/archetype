#!/usr/bin/env bash
set -euo pipefail

# framer-deploy.sh
# Pulls a Framer site, strips Framer branding, and prepares it for GitHub Pages deployment.
#
# Usage:
#   ./scripts/framer-deploy.sh <framer-url> <output-dir> [--cname <domain>]
#
# Examples:
#   ./scripts/framer-deploy.sh https://thankful-apartment-080430.framer.app/ ./site
#   ./scripts/framer-deploy.sh https://my-site.framer.app/ ./site --cname archetype.dev

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

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Use a temp file for the raw HTML (avoids shell variable mangling of large HTML)
TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

echo "Fetching $FRAMER_URL ..."
curl -sL "$FRAMER_URL" -o "$TMPFILE"

if [[ ! -s "$TMPFILE" ]]; then
  echo "Error: Failed to fetch HTML from $FRAMER_URL"
  exit 1
fi

echo "Stripping Framer branding..."

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

# 1. Remove the Framer editor script loader in <head>
html = re.sub(
    r'<script>try\{if\(localStorage\.get\("__framer_force_showing_editorbar_since"\)\).*?</script>',
    '',
    html,
    flags=re.DOTALL
)

# 2. Remove Framer search index meta tags
html = re.sub(r'\s*<meta name="framer-search-index"[^>]*>', '', html)
html = re.sub(r'\s*<meta name="framer-search-index-fallback"[^>]*>', '', html)

# 3. Remove the entire __framer-badge-container div and everything inside it
#    The badge is at the end of <body> - we match from opening div to the </body> tag
#    and keep only the </body> tag
html = re.sub(
    r'<div id="__framer-badge-container">.*?(?=</body>)',
    '',
    html,
    flags=re.DOTALL
)

# 4. Remove the CSS for the badge container
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

# 5. Remove badge-related CSS class definitions
html = re.sub(r'\.__framer-badge[^{]*\{[^}]*\}', '', html)
# Remove the badge component CSS (framer-6jWyo namespace)
html = re.sub(r'\.framer-6jWyo[^{]*\{[^}]*\}', '', html)

# 6. Remove the "Made in Framer" HTML comments
html = re.sub(r'<!--\s*Made in Framer.*?-->\n?', '', html)
html = re.sub(r'<!--\s*Published.*?-->\n?', '', html)

# 7. Remove Framer generator meta tag
html = re.sub(r'\s*<meta name="generator" content="Framer[^"]*">', '', html)

# 8. Replace Framer URLs with custom domain if provided
if cname:
    custom_url = f"https://{cname}"
    html = html.replace(framer_url, custom_url)

# Clean up excessive blank lines
html = re.sub(r'\n{3,}', '\n\n', html)

with open(output_file, "w") as f:
    f.write(html)

final_size = len(html)
print(f"  Original: {original_size:,} bytes")
print(f"  Cleaned:  {final_size:,} bytes")
print(f"  Removed:  {original_size - final_size:,} bytes")
PYEOF

echo "Created $OUTPUT_DIR/index.html"

# Create CNAME if custom domain provided
if [[ -n "$CNAME" ]]; then
  echo "$CNAME" > "$OUTPUT_DIR/CNAME"
  echo "Created $OUTPUT_DIR/CNAME (${CNAME})"
fi

# Create .nojekyll so GitHub Pages serves files as-is
touch "$OUTPUT_DIR/.nojekyll"
echo "Created $OUTPUT_DIR/.nojekyll"

# Verification
echo ""
WARNINGS=0

if grep -q '__framer-badge-container' "$OUTPUT_DIR/index.html"; then
  echo "WARNING: Framer badge container still present"
  WARNINGS=$((WARNINGS + 1))
else
  echo "OK: Framer badge removed"
fi

if grep -q 'framer.com/edit' "$OUTPUT_DIR/index.html"; then
  echo "WARNING: Framer editor references still present"
  WARNINGS=$((WARNINGS + 1))
else
  echo "OK: Framer editor scripts removed"
fi

if grep -q 'framer-search-index' "$OUTPUT_DIR/index.html"; then
  echo "WARNING: Framer search index meta tags still present"
  WARNINGS=$((WARNINGS + 1))
else
  echo "OK: Framer search index removed"
fi

if grep -q 'name="generator"' "$OUTPUT_DIR/index.html"; then
  echo "WARNING: Framer generator meta tag still present"
  WARNINGS=$((WARNINGS + 1))
else
  echo "OK: Framer generator tag removed"
fi

echo ""
if [[ $WARNINGS -eq 0 ]]; then
  echo "All clean. Ready for GitHub Pages."
else
  echo "$WARNINGS warning(s). Manual cleanup may be needed."
fi
