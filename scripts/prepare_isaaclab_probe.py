"""Generate an experimental IsaacSim-only manifest without editing upstream.

This prepares resolver diagnostics, not a validated ProtoMotions environment.
Run the printed dry-run command before considering installation.
"""
import argparse
from pathlib import Path
import re
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def prepare(destination: Path):
    source = ROOT / 'external/IsaacLab'
    pins = tomllib.loads((ROOT / 'dependencies.toml').read_text())
    pin = pins['repositories']['IsaacLab']['commit']
    head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if head != pin:
        raise SystemExit(f'Expected IsaacLab {pin}, found {head}')
    original = (source / 'pyproject.toml').read_text()
    metadata = tomllib.loads(original)
    # Preserve base requirements and all version bounds. Express architecture
    # alternatives explicitly to avoid the reproduced string-membership overlap.
    text = re.sub(r"platform_machine in '([^']+)'", lambda m: '(' + ' or '.join(
        f"platform_machine == '{value}'" for value in m[1].split()) + ')', original)
    text = text.replace('path = "source/', f'path = "{source}/source/')
    text, count = re.subn(r'\[project.optional-dependencies\].*?(?=\[tool.isaaclab.versions\])',
        '[project.optional-dependencies]\nisaacsim = ["isaacsim[all,extscache]==6.0.0.1"]\n\n', text, flags=re.S)
    if count != 1:
        raise SystemExit('Unexpected upstream manifest structure')
    text, count = re.subn(r'\nconflicts = \[.*?\n\]', '\nconflicts = []', text, flags=re.S)
    if count != 1:
        raise SystemExit('Unexpected upstream conflicts table')
    derived = tomllib.loads(text)
    assert derived['project']['optional-dependencies']['isaacsim'] == metadata['project']['optional-dependencies']['isaacsim']
    assert derived['tool']['uv']['override-dependencies'] == metadata['tool']['uv']['override-dependencies']
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / 'pyproject.toml'
    if target.exists() and target.read_text() != text:
        raise SystemExit(f'Refusing to overwrite different manifest: {target}')
    target.write_text(text)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    target = prepare(args.output.resolve())
    print(f'Prepared experimental manifest: {target}')
    print('Run uv sync --project <output-directory> --extra isaacsim --dry-run')
