#!/bin/sh
# install.sh: use these hooks in the given repos (default: ccnix, ccnix-mod
# and ccnix-claude beside this one), by pointing their core.hooksPath here.
#
#   githooks/install.sh [repo...]
#
# The sensitive list, ~/.config/ccnix-claude/sensitive.txt, is yours to
# fill: one regular expression per line for what must never be published.
set -e
here=$(cd "$(dirname "$0")" && pwd)
top=$(cd "$here/../.." && pwd)
[ $# -gt 0 ] || set -- "$top/ccnix" "$top/ccnix-mod" "$top/ccnix-claude"
for r in "$@"; do
    git -C "$r" config core.hooksPath "$here"
    echo "$r: hooks from $here"
done
list="$HOME/.config/ccnix-claude/sensitive.txt"
[ -f "$list" ] || { mkdir -p "$(dirname "$list")"; printf '%s\n' '# one regular expression per line: what must never be published' > "$list"; echo "made $list: fill it in"; }
