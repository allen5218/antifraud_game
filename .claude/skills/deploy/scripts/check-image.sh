#!/usr/bin/env bash
# 檢查 GHCR 上某個 tag 的 image index 及其所有子 manifest 是否完整。
#
# 為什麼需要:多架構鏡像的 tag 只掛在 image index 上,各架構的子 manifest 永遠 untagged。
# 若有人刪掉 GitHub Packages 的 "untagged" 版本,index 仍回 200,但子 manifest 全 404,
# `docker pull` 只會說 `manifest unknown`。只驗 index 會誤判鏡像健康。
#
# 用法: bash check-image.sh <owner>/<repo>-backend [tag]
# exit 0 = 完整可拉;exit 1 = 懸空或取不到
set -uo pipefail

REPO=${1:?用法: bash check-image.sh <owner>/<repo>-backend [tag]}
TAG=${2:-latest}

TOK=$(curl -s "https://ghcr.io/token?scope=repository:${REPO}:pull&service=ghcr.io" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin).get("token",""))')
if [ -z "$TOK" ]; then
  echo "✗ 取不到 pull token(private 鏡像?先 docker login ghcr.io)"; exit 1
fi

IDX=$(mktemp)
trap 'rm -f "$IDX"' EXIT
code=$(curl -s -o "$IDX" -w '%{http_code}' -H "Authorization: Bearer $TOK" \
  -H 'Accept: application/vnd.oci.image.index.v1+json' \
  "https://ghcr.io/v2/${REPO}/manifests/${TAG}")
echo "index ${REPO}:${TAG} → HTTP ${code}"
[ "$code" = "200" ] || { echo "✗ index 取不到"; exit 1; }

python3 - "$REPO" "$TOK" "$IDX" <<'PY'
import json, subprocess, sys
repo, tok, idx_path = sys.argv[1], sys.argv[2], sys.argv[3]
idx = json.load(open(idx_path))
manifests = idx.get("manifests")
if not manifests:
    print("  (單一架構 manifest,無子項)"); raise SystemExit(0)
bad = 0
for m in manifests:
    code = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
         "-H", f"Authorization: Bearer {tok}",
         "-H", "Accept: application/vnd.oci.image.manifest.v1+json",
         f"https://ghcr.io/v2/{repo}/manifests/{m['digest']}"],
        capture_output=True, text=True).stdout
    p = m.get("platform", {})
    kind = "attestation" if p.get("os") == "unknown" else f"{p.get('os')}/{p.get('architecture')}"
    print(f"  child {kind:16s} {m['digest'][:19]} → HTTP {code}")
    if code != "200":
        bad += 1
if bad:
    print(f"✗ 懸空 index:{bad} 個子 manifest 缺失。重跑 `gh workflow run build.yml --ref main`")
    print("  (注意:重跑只修好該次 run 產生的 tag,舊 tag 永遠指向舊的懸空 index)")
    raise SystemExit(1)
print("✓ index 與所有子 manifest 完整,可以 docker pull")
PY
