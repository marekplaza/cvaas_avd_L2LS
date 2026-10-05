#!/usr/bin/env bash
# Download a cEOS-lab image from arista.com and import it into Docker.
#
# Uses curl instead of ardl: arista.com currently answers Python HTTP clients
# with a "Client Challenge" page, which breaks ardl (eos-downloader).
#
# Usage:
#   export ARISTA_TOKEN=<token from arista.com -> My Profile -> Access Token>
#   ./get_ceos.sh                 # latest M release
#   ./get_ceos.sh -r F            # latest F release
#   ./get_ceos.sh -v 4.34.2F      # specific version
#   ./get_ceos.sh -6 -t latest    # cEOS64, also tag the image as arista/ceos:latest
#
# Options:
#   -v VERSION   EOS version (e.g. 4.35.6M); default: latest of the release type
#   -r TYPE      release type when -v is not given: M or F (default: M)
#   -6           download cEOS64 instead of cEOS
#   -o DIR       download directory (default: /tmp)
#   -t TAG       additional Docker tag (e.g. latest)
#   -n           only print what would be downloaded
set -euo pipefail

API=https://www.arista.com/custom_data/api/cvp
VERSION="" RTYPE=M PREFIX=cEOS-lab OUTDIR=/tmp EXTRA_TAG="" DRY=0

while getopts "v:r:6o:t:nh" opt; do
    case $opt in
        v) VERSION=$OPTARG ;;
        r) RTYPE=${OPTARG^^} ;;
        6) PREFIX=cEOS64-lab ;;
        o) OUTDIR=$OPTARG ;;
        t) EXTRA_TAG=$OPTARG ;;
        n) DRY=1 ;;
        *) sed -n '2,22p' "$0"; exit 1 ;;
    esac
done

: "${ARISTA_TOKEN:?set ARISTA_TOKEN (arista.com -> My Profile -> Access Token)}"
for cmd in curl python3 docker; do
    command -v "$cmd" >/dev/null || { echo "missing: $cmd" >&2; exit 1; }
done

api() { # api <endpoint> <json-body> -> response JSON on stdout
    curl -sS --fail --max-time 120 -X POST "$API/$1/" -H "Content-Type: application/json" -d "$2"
}
json() { # json <python-expression on d> -> reads JSON from stdin
    python3 -c "import sys,json; d=json.load(sys.stdin); print($1)"
}

echo ">> Authenticating"
resp=$(api getSessionCode "{\"accessToken\":\"$(printf %s "$ARISTA_TOKEN" | base64 -w0)\"}")
session=$(json 'd.get("data",{}).get("session_code","")' <<<"$resp")
[ -n "$session" ] || { echo "Authentication failed: $(json 'd["status"]["message"]' <<<"$resp")" >&2; exit 1; }

echo ">> Reading software catalog"
path=$(api getFolderTree "{\"sessionCode\":\"$session\"}" | PREFIX=$PREFIX VERSION=$VERSION RTYPE=$RTYPE python3 -c '
import json, os, re, sys
xml = json.load(sys.stdin)["data"]["xml"]
prefix, version, rtype = os.environ["PREFIX"], os.environ["VERSION"], os.environ["RTYPE"]
files = {}
for p in re.findall(r"path=\"([^\"]+)\"", xml):
    m = re.search(re.escape(prefix) + r"-(\d+)\.(\d+)\.(\d+)([A-Z])\.tar\.xz$", p)
    if m:
        files[tuple(int(x) for x in m.groups()[:3]) + (m.group(4),)] = p
if version:
    match = [p for k, p in files.items() if "%d.%d.%d%s" % k == version]
else:
    match = [files[k] for k in sorted(k for k in files if k[3] == rtype)[-1:]]
print(match[0] if match else "")')
[ -n "$path" ] || { echo "No ${PREFIX} image found for ${VERSION:-latest $RTYPE release}" >&2; exit 1; }

file=${path##*/}
ver=${file#"$PREFIX"-}; ver=${ver%.tar.xz}
image=arista/ceos:$ver
[ "$PREFIX" = cEOS64-lab ] && image=arista/ceos64:$ver
echo ">> Selected $file -> $image"
[ "$DRY" = 1 ] && exit 0

if docker image inspect "$image" >/dev/null 2>&1; then
    echo ">> $image already exists in Docker, skipping download"
else
    if [ ! -s "$OUTDIR/$file" ]; then
        url=$(api getDownloadLink "{\"sessionCode\":\"$session\",\"filePath\":\"$path\"}" | json 'd["data"]["url"]')
        echo ">> Downloading to $OUTDIR/$file"
        curl --fail --progress-bar -o "$OUTDIR/$file.part" "$url"
        mv "$OUTDIR/$file.part" "$OUTDIR/$file"
    fi
    echo ">> Importing into Docker"
    docker import "$OUTDIR/$file" "$image"
fi

if [ -n "$EXTRA_TAG" ]; then
    docker tag "$image" "${image%:*}:$EXTRA_TAG"
    echo ">> Tagged ${image%:*}:$EXTRA_TAG"
fi
docker images "${image%:*}"
