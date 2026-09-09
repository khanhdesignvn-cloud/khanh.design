#!/usr/bin/env bash
# Consistent quiesced snapshot of D1 + R2, followed by isolated restore.
set -euo pipefail
umask 077
backup_root=/var/backups/khanh-design
mkdir -p "$backup_root"
exec 9>"$backup_root/.backup.lock"
flock -n 9 || { printf 'Another backup is running\n' >&2; exit 1; }
stamp=$(date -u +%Y%m%dT%H%M%S)-$$
tmp=$(mktemp -d "$backup_root/.tmp-$stamp-XXXXXX")
snapshot="$backup_root/snapshot-$stamp"
latest="$backup_root/latest"
stopped=0
cleanup(){
  result=$?
  if [ "$stopped" = 1 ]; then systemctl start khanh-design.service || result=1; fi
  rm -rf -- "$tmp"
  exit "$result"
}
trap cleanup EXIT
# Do not accidentally start a service an operator deliberately left stopped.
systemctl is-active --quiet khanh-design.service
stopped=1
systemctl stop khanh-design.service
if [ -L "$latest" ] && [ -d "$(readlink -f "$latest")/state" ]; then
  previous="$(readlink -f "$latest")/state"
  rsync -a --link-dest="$previous" /var/lib/khanh-design/ "$tmp/state/"
else
  rsync -a /var/lib/khanh-design/ "$tmp/state/"
fi
rsync -a /etc/khanh-design/ "$tmp/config/"
readlink -f /opt/khanh-design/current > "$tmp/release.txt"
systemctl start khanh-design.service
stopped=0
curl --retry 30 --retry-connrefused --retry-delay 1 --max-time 2 -fsS http://127.0.0.1:8794/api/workspace >/dev/null
/usr/local/sbin/verify-mindmap-backup "$tmp" > "$tmp/restore-verification.json"
# Python hashes all files, including copied config, without logging contents.
python3 - "$tmp" <<'PY'
import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1])
manifest={}
for p in sorted(root.rglob('*')):
    if p.is_file():
        with p.open('rb') as f: manifest[str(p.relative_to(root))]=hashlib.file_digest(f,'sha256').hexdigest()
(root/'manifest.json').write_text(json.dumps(manifest,sort_keys=True))
for name,expected in manifest.items():
    with (root/name).open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==expected
PY
mv "$tmp" "$snapshot"
ln -sfn "$snapshot" "$latest.new"
mv -Tf "$latest.new" "$latest"
# No automatic pruning: retain ALL snapshots (at least 30 as days accumulate).
# This deliberately preserves historical tar archives and avoids unsafe deletion.
printf 'Backup and isolated restore verified: %s\n' "$snapshot"
