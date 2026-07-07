from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def run_df(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'tools'}{os.pathsep}{ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"
    proc = subprocess.run(
        ["python3", "-m", "dark_factory", *args],
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
    )
    if check and proc.returncode != 0:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "df@example.test"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Dark Factory"], cwd=path, check=True)


def copy_skill_template(repo: Path) -> None:
    target = repo / "skills" / "df-spec" / "templates"
    target.mkdir(parents=True)
    shutil.copyfile(ROOT / "skills" / "df-spec" / "templates" / "state-template.md", target / "state-template.md")


class CliPrimitiveTests(unittest.TestCase):
    def test_state_and_evidence_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            copy_skill_template(tmp_path)

            run_df(tmp_path, "state", "init", "OFRS2-1", "--title", "Add Toggle")
            title = run_df(tmp_path, "state", "get", "OFRS2-1", "title").stdout.strip()
            self.assertEqual(title, "Add Toggle")

            evidence = tmp_path / "docs" / "specs" / "OFRS2-1-add-toggle" / "evidence" / "unit"
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "ac-1.txt").write_text("pytest passed\n", encoding="utf-8")
            (evidence / "ac-1.txt.yaml").write_text("criterion: AC-1 toggle works\n", encoding="utf-8")

            run_df(tmp_path, "evidence", "index", "OFRS2-1")
            index = (evidence.parent / "INDEX.md").read_text(encoding="utf-8")
            self.assertIn("AC-1 toggle works", index)
            self.assertIn("unit/ac-1.txt", index)

    def test_state_block_and_unblock_resumes_recorded_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            copy_skill_template(tmp_path)

            run_df(tmp_path, "state", "init", "OFRS2-3", "--title", "Blocked Story", "--status", "implementing")

            run_df(tmp_path, "state", "block", "OFRS2-3", "--reason", "gh auth status is unauthenticated")
            status = run_df(tmp_path, "state", "get", "OFRS2-3", "status").stdout.strip()
            self.assertEqual(status, "blocked")
            blocked_from = run_df(tmp_path, "state", "get", "OFRS2-3", "blocked_from").stdout.strip()
            self.assertEqual(blocked_from, "implementing")
            blocked_reason = run_df(tmp_path, "state", "get", "OFRS2-3", "blocked_reason").stdout.strip()
            self.assertEqual(blocked_reason, "gh auth status is unauthenticated")

            resume_proc = run_df(tmp_path, "resume", "--ticket", "OFRS2-3", check=False)
            self.assertEqual(resume_proc.returncode, 1)
            resume_output = resume_proc.stdout
            self.assertIn("next_skill=stop", resume_output)
            self.assertIn("blocked_from=implementing", resume_output)

            # Blocking again while already blocked must not clobber the original phase.
            run_df(tmp_path, "state", "block", "OFRS2-3", "--reason", "still waiting on gh auth")
            blocked_from = run_df(tmp_path, "state", "get", "OFRS2-3", "blocked_from").stdout.strip()
            self.assertEqual(blocked_from, "implementing")

            run_df(tmp_path, "state", "unblock", "OFRS2-3")
            status = run_df(tmp_path, "state", "get", "OFRS2-3", "status").stdout.strip()
            self.assertEqual(status, "implementing")
            blocked_from = run_df(tmp_path, "state", "get", "OFRS2-3", "blocked_from").stdout.strip()
            self.assertEqual(blocked_from, "")
            blocked_reason = run_df(tmp_path, "state", "get", "OFRS2-3", "blocked_reason").stdout.strip()
            self.assertEqual(blocked_reason, "")

            unblock_again = run_df(tmp_path, "state", "unblock", "OFRS2-3", check=False)
            self.assertNotEqual(unblock_again.returncode, 0)

    def test_detect_tooling_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            (tmp_path / "package.json").write_text(
                json.dumps({"scripts": {"lint": "eslint .", "test": "node --test", "build": "vite build"}}),
                encoding="utf-8",
            )
            output = run_df(tmp_path, "detect-tooling", "--json", "--no-write").stdout
            data = json.loads(output)
            self.assertEqual(data["modules"][0]["path"], ".")
            self.assertEqual(data["modules"][0]["validation_commands"]["test"], "npm test")

    def test_risk_classifier_path_matrix(self) -> None:
        from dark_factory.risk import classify_paths

        risk, reasons = classify_paths([".github/workflows/pr-checks.yml"], [])
        self.assertEqual(risk, "high")
        self.assertTrue(reasons)

        risk, reasons = classify_paths(["src/components/Button.tsx"], [])
        self.assertEqual(risk, "low")
        self.assertEqual(reasons, ["low:no high or medium risk path triggers"])

    def test_preflight_writes_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            copy_skill_template(tmp_path)
            (tmp_path / "README.md").write_text("# fixture\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
            subprocess.run(["git", "commit", "-m", "chore: initial fixture"], cwd=tmp_path, check=True)

            run_df(tmp_path, "state", "init", "OFRS2-2", "--title", "Preflight")
            run_df(tmp_path, "state", "set", "OFRS2-2", "working_root", str(tmp_path))
            state_file = tmp_path / "docs" / "specs" / "OFRS2-2-preflight" / "state.md"
            text = state_file.read_text(encoding="utf-8")
            text = text.replace("lint: command-or-empty", "lint: python3 -c 'print(\"lint\")'")
            text = text.replace("typecheck: command-or-empty", "typecheck: python3 -c 'print(\"typecheck\")'")
            text = text.replace("test: command-or-empty", "test: python3 -c 'print(\"test\")'")
            text = text.replace("build: command-or-empty", "build: python3 -c 'print(\"build\")'")
            state_file.write_text(text, encoding="utf-8")

            run_df(tmp_path, "preflight", "OFRS2-2", "--diff-base", "HEAD")
            result = json.loads(
                (tmp_path / "docs" / "specs" / "OFRS2-2-preflight" / "preflight.json").read_text()
            )
            self.assertEqual(result["summary"], "passed")
            stage_names = {stage["name"] for stage in result["stages"]}
            self.assertGreaterEqual(stage_names, {"lint", "typecheck", "test", "build", "commit-lint"})

    def _write_pr_fix_loop_workflow(self, tmp_path: Path, configured: bool) -> None:
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        flag = "true" if configured else "false"
        (workflows_dir / "pr-fix-loop.yml").write_text(
            f'env:\n  DF_MERGE_RUNTIME_CONFIGURED: "{flag}"\n',
            encoding="utf-8",
        )

    def test_doctor_flags_unconfigured_pr_fix_loop_with_eligible_story(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            copy_skill_template(tmp_path)
            self._write_pr_fix_loop_workflow(tmp_path, configured=False)

            run_df(tmp_path, "state", "init", "OFRS2-4", "--title", "Auto Merge Candidate")
            run_df(tmp_path, "state", "set", "OFRS2-4", "auto_merge_eligible", "true")
            run_df(tmp_path, "state", "set", "OFRS2-4", "status", "merging")

            result = run_df(tmp_path, "doctor", check=False)
            self.assertIn("missing\tpr-fix-loop-runtime", result.stdout)
            self.assertIn("OFRS2-4", result.stdout)

    def test_doctor_ignores_configured_pr_fix_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            copy_skill_template(tmp_path)
            self._write_pr_fix_loop_workflow(tmp_path, configured=True)

            run_df(tmp_path, "state", "init", "OFRS2-5", "--title", "Auto Merge Candidate")
            run_df(tmp_path, "state", "set", "OFRS2-5", "auto_merge_eligible", "true")
            run_df(tmp_path, "state", "set", "OFRS2-5", "status", "merging")

            result = run_df(tmp_path, "doctor", check=False)
            self.assertIn("ok\tpr-fix-loop-runtime", result.stdout)

    def test_doctor_skips_pr_fix_loop_check_without_eligible_story(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            copy_skill_template(tmp_path)
            self._write_pr_fix_loop_workflow(tmp_path, configured=False)

            result = run_df(tmp_path, "doctor", check=False)
            self.assertNotIn("pr-fix-loop-runtime", result.stdout)


if __name__ == "__main__":
    unittest.main()
