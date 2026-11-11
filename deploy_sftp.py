"""Dépose dist/ chez Infomaniak en SFTP, sans apt ni lftp.

N'envoie que les fichiers modifiés : un manifeste (.deploy.json, empreinte de chaque
fichier) est gardé sur le serveur. Les fichiers disparus de dist/ sont supprimés.
Variables : FTP_HOST, FTP_USER, FTP_PASSWORD, SITE_DIR.
"""
import hashlib, json, os, posixpath, sys
import paramiko

HOST, USER, PWD = os.environ["FTP_HOST"], os.environ["FTP_USER"], os.environ["FTP_PASSWORD"]
ROOT = os.environ.get("SITE_DIR", "sites/new.studiobega.be").rstrip("/")
DIST = "dist"
MANIFEST = ".deploy.json"


def local_files():
    out = {}
    for d, _, files in os.walk(DIST):
        for f in files:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, DIST).replace(os.sep, "/")
            with open(p, "rb") as fh:
                out[rel] = hashlib.md5(fh.read()).hexdigest()
    return out


def mkdirs(sftp, path, made):
    parts = path.split("/")
    for i in range(1, len(parts) + 1):
        sub = "/".join(parts[:i])
        if sub in made:
            continue
        try:
            sftp.stat(sub)
        except IOError:
            sftp.mkdir(sub)
        made.add(sub)


def main():
    t = paramiko.Transport((HOST, 22))
    t.connect(username=USER, password=PWD)
    sftp = paramiko.SFTPClient.from_transport(t)

    try:
        with sftp.open(f"{ROOT}/{MANIFEST}") as fh:
            remote = json.load(fh)
    except (IOError, ValueError):
        remote = {}  # premier passage : tout est envoyé

    local = local_files()
    changed = [r for r, h in local.items() if remote.get(r) != h]
    gone = [r for r in remote if r not in local]

    made = set()
    for rel in sorted(changed):
        dest = f"{ROOT}/{rel}"
        mkdirs(sftp, posixpath.dirname(dest), made)
        sftp.put(os.path.join(DIST, rel), dest)
    for rel in gone:
        try:
            sftp.remove(f"{ROOT}/{rel}")
        except IOError:
            pass

    with sftp.open(f"{ROOT}/{MANIFEST}", "w") as fh:
        fh.write(json.dumps(local))
    sftp.close(); t.close()
    print(f"{len(changed)} fichier(s) envoyé(s), {len(gone)} supprimé(s), {len(local)} en ligne")


if __name__ == "__main__":
    sys.exit(main())
