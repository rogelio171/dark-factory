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


class ObservabilityTests(unittest.TestCase):
    def test_init_and_doctor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            output = run_df(tmp_path, "observability", "init").stdout.strip()
            self.assertTrue(Path(output).exists())
            doctor = run_df(tmp_path, "observability", "doctor", check=False)
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            self.assertIn("observability-db", doctor.stdout)
            gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("observability.db", gitignore)

    def test_run_session_message_event_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            run_df(tmp_path, "observability", "init")
            run_json = json.loads(run_df(tmp_path, "observability", "run", "start", "OFRS2-9", "--story-slug", "OFRS2-9-test").stdout)
            run_id = run_json["run_id"]
            session_json = json.loads(
                run_df(
                    tmp_path,
                    "observability",
                    "session",
                    "start",
                    "--run-id",
                    run_id,
                    "--skill",
                    "df-spec",
                    "--role",
                    "coordinator",
                ).stdout
            )
            session_id = session_json["session_id"]
            run_df(
                tmp_path,
                "observability",
                "message",
                "record",
                "--session-id",
                session_id,
                "--role",
                "user",
                "--content",
                "Please implement the toggle",
            )
            run_df(
                tmp_path,
                "observability",
                "message",
                "record",
                "--session-id",
                session_id,
                "--role",
                "assistant",
                "--content",
                "I will implement the toggle",
                "--tool-name",
                "Shell",
                "--tool-call-id",
                "call-1",
            )
            run_df(
                tmp_path,
                "observability",
                "event",
                "record",
                "--run-id",
                run_id,
                "--category",
                "workflow.phase",
                "--action",
                "phase.transition",
                "--ticket",
                "OFRS2-9",
                "--summary",
                "Moved to specifying",
            )
            run_df(
                tmp_path,
                "observability",
                "snapshot",
                "record",
                "--source",
                "jira",
                "--snapshot-type",
                "issue_fetch",
                "--reference",
                "OFRS2-9",
                "--payload",
                '{"summary":"Add toggle"}',
                "--run-id",
                run_id,
            )
            tail = run_df(tmp_path, "observability", "tail", "--run-id", run_id, "--limit", "10").stdout
            self.assertIn("workflow.phase", tail)
            session = json.loads(run_df(tmp_path, "observability", "session", "show", session_id).stdout)
            self.assertEqual(len(session["messages"]), 2)
            run_df(tmp_path, "observability", "session", "end", "--session-id", session_id)
            run_df(tmp_path, "observability", "run", "end", "--run-id", run_id, "--status", "complete")

    def test_redaction(self) -> None:
        from dark_factory.observability.config import load_config
        from dark_factory.observability.redaction import redact_text

        config = load_config()
        redacted = redact_text("token=ghp_abcdefghijklmnopqrstuvwxyz1234567890", config)
        self.assertIn("[REDACTED]", redacted)
        self.assertNotIn("ghp_", redacted)

    def test_batch_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            run_df(tmp_path, "observability", "init")
            batch_file = tmp_path / "batch.jsonl"
            batch_file.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "run_start", "ticket": "OFRS2-2", "story_slug": "OFRS2-2-batch"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            counts = json.loads(run_df(tmp_path, "observability", "batch", "--file", str(batch_file)).stdout)
            self.assertEqual(counts["runs"], 1)
            export_dir = tmp_path / ".agents" / "dark-factory" / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            export_path = export_dir / "out.jsonl"
            result = json.loads(
                run_df(
                    tmp_path,
                    "observability",
                    "export",
                    "--ticket",
                    "OFRS2-2",
                    "--output",
                    str(export_path),
                ).stdout
            )
            self.assertGreater(result["record_count"], 0)
            self.assertTrue(export_path.exists())

    def test_story_init_sets_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            copy_skill_template(tmp_path)
            run_df(tmp_path, "observability", "init")
            run_df(tmp_path, "story", "init", "OFRS2-3", "--title", "Batch Story", "--no-branch")
            run_id = run_df(tmp_path, "state", "get", "OFRS2-3", "run_id").stdout.strip()
            self.assertTrue(run_id)
            enabled = run_df(tmp_path, "state", "get", "OFRS2-3", "observability_enabled").stdout.strip()
            self.assertEqual(enabled, "True")

    def test_cli_auto_logs_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            run_df(tmp_path, "observability", "init")
            run_df(tmp_path, "observability", "stats")
            stats = json.loads(run_df(tmp_path, "observability", "stats").stdout)
            self.assertGreaterEqual(stats["interaction_events"]["count"], 1)

    def test_report_and_prune_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            run_df(tmp_path, "observability", "init")
            run_df(tmp_path, "observability", "run", "start", "OFRS2-4")
            report = json.loads(run_df(tmp_path, "observability", "report", "--since", "30d").stdout)
            self.assertIn("runs_by_status", report)
            dry = json.loads(run_df(tmp_path, "observability", "prune", "--dry-run").stdout)
            self.assertTrue(dry["dry_run"])

    def test_export_scopes_snapshots_by_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            run_df(tmp_path, "observability", "init")
            run_a = json.loads(run_df(tmp_path, "observability", "run", "start", "TICKET-A").stdout)["run_id"]
            run_b = json.loads(run_df(tmp_path, "observability", "run", "start", "TICKET-B").stdout)["run_id"]
            run_df(
                tmp_path,
                "observability",
                "snapshot",
                "record",
                "--source",
                "github",
                "--snapshot-type",
                "pr_poll",
                "--reference",
                "1",
                "--payload",
                '{"ticket":"A"}',
                "--run-id",
                run_a,
            )
            run_df(
                tmp_path,
                "observability",
                "snapshot",
                "record",
                "--source",
                "github",
                "--snapshot-type",
                "pr_poll",
                "--reference",
                "2",
                "--payload",
                '{"ticket":"B"}',
                "--run-id",
                run_b,
            )
            export_path = tmp_path / "a.jsonl"
            json.loads(
                run_df(
                    tmp_path,
                    "observability",
                    "export",
                    "--ticket",
                    "TICKET-A",
                    "--no-messages",
                    "--output",
                    str(export_path),
                ).stdout
            )
            lines = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            snapshots = [line for line in lines if line.get("record_type") == "snapshot"]
            self.assertEqual(len(snapshots), 1)
            self.assertEqual(json.loads(snapshots[0]["payload_json"])["ticket"], "A")

    def test_cli_summary_redacts_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            copy_skill_template(tmp_path)
            run_df(tmp_path, "observability", "init")
            token = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
            run_df(tmp_path, "story", "init", "OFRS2-6", "--title", "Redact", "--no-branch")
            run_df(tmp_path, "state", "set", "OFRS2-6", "phase_detail", token, check=False)
            events = json.loads(
                run_df(
                    tmp_path,
                    "observability",
                    "query",
                    "--ticket",
                    "OFRS2-6",
                    "--category",
                    "cli.command",
                    "--json",
                ).stdout
            )
            self.assertTrue(events)
            combined = json.dumps(events)
            self.assertNotIn(token, combined)
            self.assertIn("[REDACTED]", events[0]["summary"])

    def test_state_phase_transition_logs_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            init_repo(tmp_path)
            copy_skill_template(tmp_path)
            run_df(tmp_path, "observability", "init")
            run_df(tmp_path, "story", "init", "OFRS2-5", "--title", "Phase Log", "--no-branch")
            run_id = run_df(tmp_path, "state", "get", "OFRS2-5", "run_id").stdout.strip()
            run_df(tmp_path, "state", "set", "OFRS2-5", "status", "workspace")
            events = json.loads(
                run_df(
                    tmp_path,
                    "observability",
                    "query",
                    "--run-id",
                    run_id,
                    "--category",
                    "workflow.phase",
                    "--json",
                ).stdout
            )
            actions = {event["action"] for event in events}
            self.assertIn("phase.transition", actions)


if __name__ == "__main__":
    unittest.main()
