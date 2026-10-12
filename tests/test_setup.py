import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETUP_SCRIPT = PROJECT_ROOT / "scripts" / "setup.py"


def run(
    *args: str,
    cwd: Path,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )


class SetupCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self._temporary_directory.name)
        self.project = self.base / "project"
        (self.project / "scripts").mkdir(parents=True)
        shutil.copy2(SETUP_SCRIPT, self.project / "scripts" / "setup.py")

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def make_remote(self, name: str, *, lfs: bool = False) -> tuple[Path, str]:
        work = self.base / f"{name}-work"
        remote = self.base / f"{name}.git"
        work.mkdir()
        run("git", "init", "-q", cwd=work)
        run("git", "config", "user.name", "ProtoLab Test", cwd=work)
        run("git", "config", "user.email", "test@protolab.invalid", cwd=work)
        (work / "README.md").write_text(f"{name}\n")
        if lfs:
            run("git", "lfs", "install", "--local", cwd=work)
            run("git", "lfs", "track", "payload.bin", cwd=work)
            (work / "payload.bin").write_bytes(b"fixture-lfs-payload\n")
            run("git", "add", ".gitattributes", "payload.bin", cwd=work)
        else:
            run("git", "add", "README.md", cwd=work)
        run("git", "commit", "-qm", "fixture", cwd=work)
        commit = run("git", "rev-parse", "HEAD", cwd=work).stdout.strip()
        run("git", "clone", "-q", "--bare", str(work), str(remote), cwd=self.base)
        if lfs:
            shutil.copytree(work / ".git" / "lfs", remote / "lfs", dirs_exist_ok=True)
        return remote, commit

    def write_dependencies(self, repositories: dict[str, tuple[Path, str]]) -> None:
        entries = []
        for name, (remote, commit) in repositories.items():
            entries.append(
                textwrap.dedent(
                    f'''\
                    [repositories.{name}]
                    url = "{remote}"
                    commit = "{commit}"
                    '''
                )
            )
        (self.project / "dependencies.toml").write_text("\n".join(entries))

    def setup(
        self,
        *args: str,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return run(
            "python3",
            "scripts/setup.py",
            *args,
            cwd=self.project,
            check=check,
            env=env,
        )

    def test_check_reports_missing_uv_prerequisite(self) -> None:
        tools = self.base / "tools"
        tools.mkdir()
        (tools / "python3").symlink_to(shutil.which("python3"))
        (tools / "git").symlink_to(shutil.which("git"))
        environment = dict(os.environ, PATH=str(tools))

        result = self.setup("--check", check=False, env=environment)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Required tool missing: uv", result.stdout)

    def test_setup_clones_all_missing_sources_and_is_repeatable(self) -> None:
        repositories = {
            "IsaacLab": self.make_remote("IsaacLab"),
            "ProtoMotions": self.make_remote("ProtoMotions"),
        }
        self.write_dependencies(repositories)

        first = self.setup()
        second = self.setup()

        for name, (_, commit) in repositories.items():
            checkout = self.project / "external" / name
            self.assertEqual(
                run("git", "rev-parse", "HEAD", cwd=checkout).stdout.strip(),
                commit,
            )
            self.assertIn(f"{name}: prepared {commit}", first.stdout)
            self.assertIn(f"{name}: verified {commit}", second.stdout)
        self.assertFalse((self.project / ".venv").exists())

    def test_check_rejects_checkout_with_missing_lfs_payload(self) -> None:
        remote, commit = self.make_remote("ProtoMotions", lfs=True)
        self.write_dependencies({"ProtoMotions": (remote, commit)})
        checkout = self.project / "external" / "ProtoMotions"
        checkout.parent.mkdir()
        environment = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1")
        run("git", "clone", "-q", str(remote), str(checkout), cwd=self.base, env=environment)

        result = self.setup("--check", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not materialized", result.stdout)

    def test_check_rejects_pointer_only_worktree_even_when_object_is_cached(self) -> None:
        remote, commit = self.make_remote("ProtoMotions", lfs=True)
        self.write_dependencies({"ProtoMotions": (remote, commit)})
        self.setup()
        checkout = self.project / "external" / "ProtoMotions"
        pointer = run("git", "show", "HEAD:payload.bin", cwd=checkout).stdout
        (checkout / "payload.bin").write_text(pointer)
        run("git", "update-index", "--assume-unchanged", "payload.bin", cwd=checkout)

        result = self.setup("--check", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not materialized", result.stdout)

    def test_check_does_not_mutate_corrupt_lfs_cache(self) -> None:
        remote, commit = self.make_remote("ProtoMotions", lfs=True)
        self.write_dependencies({"ProtoMotions": (remote, commit)})
        self.setup()
        checkout = self.project / "external" / "ProtoMotions"
        listing = json.loads(run("git", "lfs", "ls-files", "--json", cwd=checkout).stdout)
        oid = listing["files"][0]["oid"]
        git_directory = Path(run("git", "rev-parse", "--git-dir", cwd=checkout).stdout.strip())
        location = checkout / git_directory / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
        location.write_bytes(b"corrupt-lfs-cache\n")
        corrupt_contents = location.read_bytes()

        result = self.setup("--check", check=False)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn(f"ProtoMotions: verified {commit}", result.stdout)
        self.assertTrue(location.exists())
        self.assertEqual(location.read_bytes(), corrupt_contents)

    def test_setup_fetches_missing_lfs_payload_for_valid_checkout(self) -> None:
        remote, commit = self.make_remote("ProtoMotions", lfs=True)
        self.write_dependencies({"ProtoMotions": (remote, commit)})
        checkout = self.project / "external" / "ProtoMotions"
        checkout.parent.mkdir()
        environment = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1")
        run("git", "clone", "-q", str(remote), str(checkout), cwd=self.base, env=environment)
        self.assertTrue((checkout / "payload.bin").read_text().startswith("version https://"))

        result = self.setup()

        self.assertEqual((checkout / "payload.bin").read_bytes(), b"fixture-lfs-payload\n")
        self.assertIn(f"ProtoMotions: prepared {commit}", result.stdout)

    def test_check_accepts_a_complete_pinned_checkout(self) -> None:
        remote, commit = self.make_remote("ProtoMotions", lfs=True)
        self.write_dependencies({"ProtoMotions": (remote, commit)})
        self.setup()

        result = self.setup("--check")

        self.assertIn(f"ProtoMotions: verified {commit}", result.stdout)

    def test_check_reports_a_missing_checkout_without_creating_it(self) -> None:
        remote, commit = self.make_remote("ProtoMotions")
        self.write_dependencies({"ProtoMotions": (remote, commit)})

        result = self.setup("--check", check=False)

        checkout = self.project / "external" / "ProtoMotions"
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"Missing checkout: {checkout}", result.stdout)
        self.assertFalse(checkout.exists())

    def test_check_rejects_checkout_at_wrong_revision(self) -> None:
        remote, commit = self.make_remote("ProtoMotions")
        self.write_dependencies({"ProtoMotions": (remote, commit)})
        self.setup()
        checkout = self.project / "external" / "ProtoMotions"
        run("git", "config", "user.name", "ProtoLab Test", cwd=checkout)
        run("git", "config", "user.email", "test@protolab.invalid", cwd=checkout)
        run("git", "commit", "--allow-empty", "-qm", "different revision", cwd=checkout)

        result = self.setup("--check", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"must be at {commit}", result.stdout)

    def test_check_rejects_checkout_with_local_changes(self) -> None:
        remote, commit = self.make_remote("ProtoMotions")
        self.write_dependencies({"ProtoMotions": (remote, commit)})
        self.setup()
        checkout = self.project / "external" / "ProtoMotions"
        (checkout / "README.md").write_text("local work\n")

        result = self.setup("--check", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Checkout has local changes", result.stdout)

    def test_check_rejects_checkout_with_unexpected_origin(self) -> None:
        remote, commit = self.make_remote("ProtoMotions")
        other_remote, _ = self.make_remote("Other")
        self.write_dependencies({"ProtoMotions": (remote, commit)})
        self.setup()
        checkout = self.project / "external" / "ProtoMotions"
        run("git", "remote", "set-url", "origin", str(other_remote), cwd=checkout)

        result = self.setup("--check", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unexpected origin", result.stdout)

    def test_setup_validates_every_existing_checkout_before_cloning(self) -> None:
        missing_remote, missing_commit = self.make_remote("Missing")
        dirty_remote, dirty_commit = self.make_remote("Dirty")
        self.write_dependencies(
            {
                "Missing": (missing_remote, missing_commit),
                "Dirty": (dirty_remote, dirty_commit),
            }
        )
        dirty_checkout = self.project / "external" / "Dirty"
        dirty_checkout.parent.mkdir()
        run("git", "clone", "-q", str(dirty_remote), str(dirty_checkout), cwd=self.base)
        (dirty_checkout / "README.md").write_text("local work\n")

        result = self.setup(check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Checkout has local changes", result.stdout)
        self.assertFalse((self.project / "external" / "Missing").exists())


if __name__ == "__main__":
    unittest.main()
