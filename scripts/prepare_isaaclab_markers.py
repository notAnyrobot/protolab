"""Copy the pinned IsaacLab manifest with narrowly scoped resolver corrections.

The generated directory is a resolver probe, not a validated installation.
Correct two pytetwild markers; optionally exclude the unused standalone ov extra.
An opt-in MoviePy source migration replaces its 1.x bound for Pillow 12 support.
Other requirements, indexes and overrides remain unchanged.
"""

import argparse
from pathlib import Path
import subprocess
import tomllib


ROOT = Path(__file__).resolve().parents[1]
MOVIEPY_SOURCE = "https://github.com/Zulko/moviepy/archive/97316f37f6a8d3843abfb53eba8f3bb0ea46a008.tar.gz"


def prepare(destination: Path, *, exclude_ov: bool = False, moviepy_source: bool = False) -> Path:
    source = ROOT / "external/IsaacLab"
    pin = tomllib.loads((ROOT / "dependencies.toml").read_text())["repositories"]["IsaacLab"]["commit"]
    head = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if head != pin:
        raise SystemExit(f"Expected IsaacLab {pin}, found {head}")
    if destination == source or source in destination.parents:
        raise SystemExit("Choose a destination outside the official IsaacLab checkout")

    text = (source / "pyproject.toml").read_text()
    replacements = {
        "pytetwild==0.2.3 ; platform_machine in 'x86_64 AMD64'":
            "pytetwild==0.2.3 ; platform_machine == 'x86_64' or platform_machine == 'AMD64'",
        "pytetwild[all]>=0.3.0,<0.4 ; platform_machine in 'aarch64 arm64'":
            "pytetwild[all]>=0.3.0,<0.4 ; platform_machine == 'aarch64' or platform_machine == 'arm64'",
    }
    for original, corrected in replacements.items():
        if text.count(original) != 1:
            raise SystemExit(f"Expected exactly one upstream declaration: {original}")
        text = text.replace(original, corrected)
    if exclude_ov:
        # ProtoMotions selects PhysxCfg/omni.physx, not OvPhysxCfg. Remove
        # only this unused extra and its conflict entry; keep source packages.
        for entry in (
            'ov = ["ovphysx==0.5.2+head.f62c22207c"]\n',
            '    [{ extra = "isaacsim" }, { extra = "ov" }],\n',
        ):
            if text.count(entry) != 1:
                raise SystemExit(f"Unexpected upstream ov declaration: {entry.strip()}")
            text = text.replace(entry, "")
    if moviepy_source:
        original = '"moviepy>=1.0.3,<2.0.0.dev0"'
        if text.count(original) != 1:
            raise SystemExit("Unexpected upstream MoviePy requirement")
        text = text.replace(original, f'"moviepy @ {MOVIEPY_SOURCE}"')
        text = text.replace(
            '    # bounded to the 1.x line: moviepy 2.x stable caps pillow below our pin, so\n'
            '    # prerelease-allowing resolvers fell through to the broken 2.0.0.dev2 build,\n'
            '    # whose write_videofile drops the clip fps and crashes video recording\n',
            '    # ProtoLab experiment: official MoviePy source fix supports Pillow 12.\n'
            '    # Exact source revision is intentional; this is not the PyPI 2.2.1 wheel.\n',
        )
    tomllib.loads(text)

    target = destination / "pyproject.toml"
    source_link = destination / "source"
    if target.exists() and target.read_text() != text:
        raise SystemExit(f"Refusing to overwrite different manifest: {target}")
    if source_link.exists() or source_link.is_symlink():
        if not source_link.is_symlink() or source_link.resolve() != source / "source":
            raise SystemExit(f"Refusing to replace source path: {source_link}")
    destination.mkdir(parents=True, exist_ok=True)
    if not source_link.is_symlink():
        source_link.symlink_to(source / "source", target_is_directory=True)
    target.write_text(text)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--exclude-ov", action="store_true",
        help="Exclude the standalone ov extra from resolution for Isaac Sim/PhysX use",
    )
    parser.add_argument(
        "--moviepy-source", action="store_true",
        help="Use the tested upstream MoviePy source fix compatible with Pillow 12",
    )
    args = parser.parse_args()
    print(f"Prepared manifest: {prepare(args.output.resolve(), exclude_ov=args.exclude_ov, moviepy_source=args.moviepy_source)}")
