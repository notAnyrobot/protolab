"""Prepare and verify ProtoLab's pinned external source checkouts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT, env=None):
    subprocess.run(args, cwd=cwd, env=env, check=True)


def output(*args, cwd):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def verify_lfs(path):
    listing = json.loads(output('git', 'lfs', 'ls-files', '--json', cwd=path))
    files = listing.get('files')
    if files is None:
        files = []
    if not isinstance(files, list):
        raise SystemExit(f'Unexpected `git lfs ls-files --json` output in {path}.')
    required_fields = {'name', 'size', 'oid_type', 'oid'}
    for item in files:
        if not isinstance(item, dict) or not required_fields.issubset(item):
            raise SystemExit(f'Unexpected `git lfs ls-files --json` entry in {path}.')
        payload = path / item['name']
        if not payload.is_file():
            raise SystemExit(f'{payload} is a missing Git LFS payload; run `git lfs pull` in {path}.')
        if payload.stat().st_size != item['size']:
            raise SystemExit(f'{payload} is not materialized; run `git lfs pull` in {path}.')
        if item['oid_type'] != 'sha256':
            raise SystemExit(f'Unsupported Git LFS object type {item["oid_type"]!r} for {payload}.')
        digest = hashlib.sha256()
        with payload.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != item['oid']:
            raise SystemExit(f'{payload} is a corrupt Git LFS payload; run `git lfs pull` in {path}.')


def checkout_status(path):
    index_path = Path(output('git', 'rev-parse', '--git-path', 'index', cwd=path))
    if not index_path.is_absolute():
        index_path = path / index_path
    with tempfile.TemporaryDirectory(prefix='protolab-source-check-') as temporary:
        temporary_path = Path(temporary)
        temporary_index = temporary_path / 'index'
        shutil.copy2(index_path, temporary_index)
        environment = dict(
            os.environ,
            GIT_INDEX_FILE=str(temporary_index),
            GIT_OPTIONAL_LOCKS='0',
        )
        result = subprocess.run(
            ('git', '--no-optional-locks', '-c', f'lfs.storage={temporary_path / "lfs"}', 'status', '--porcelain'),
            cwd=path,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    if result.returncode:
        raise SystemExit(f'Unable to inspect checkout state in {path}.\n{result.stdout.strip()}')
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check tools and existing source pins without downloads or changes')
    args = parser.parse_args()
    for tool in ('git', 'uv'):
        if not shutil.which(tool):
            raise SystemExit(f'Required tool missing: {tool}')
    run('git', 'lfs', 'version')
    pins = tomllib.loads((ROOT / 'dependencies.toml').read_text())['repositories']
    # Validate all existing checkouts before changing anything.
    for name, pin in pins.items():
        path = ROOT / 'external' / name
        if not path.exists():
            if args.check:
                raise SystemExit(f'Missing checkout: {path}')
            continue
        if not (path / '.git').exists():
            raise SystemExit(f'Not an independent Git checkout: {path}')
        if output('git', 'remote', 'get-url', 'origin', cwd=path) != pin['url']:
            raise SystemExit(f'Unexpected origin in {path}; inspect it manually.')
        if checkout_status(path):
            raise SystemExit(f'Checkout has local changes: {path}; preserve them before setup.')
        if output('git', 'rev-parse', 'HEAD', cwd=path) != pin['commit']:
            raise SystemExit(f'{path} must be at {pin["commit"]}; select the revision manually.')
        if args.check:
            verify_lfs(path)
        print(f'{name}: verified {pin["commit"]}', flush=True)
    print(f'Available disk space: {shutil.disk_usage(ROOT).free / 2**30:.1f} GiB', flush=True)
    if args.check:
        return
    for name, pin in pins.items():
        path = ROOT / 'external' / name
        if not path.exists():
            path.parent.mkdir(exist_ok=True)
            # Download LFS only after selecting the recorded revision.
            env = dict(os.environ, GIT_LFS_SKIP_SMUDGE='1')
            run('git', 'clone', '--no-checkout', pin['url'], str(path), env=env)
            run('git', 'checkout', '--detach', pin['commit'], cwd=path, env=env)
        run('git', 'lfs', 'pull', cwd=path)
        verify_lfs(path)
        print(f'{name}: prepared {pin["commit"]}', flush=True)
    print('External sources are ready. Run `uv sync --locked` to install ProtoLab.')


if __name__ == '__main__':
    main()
