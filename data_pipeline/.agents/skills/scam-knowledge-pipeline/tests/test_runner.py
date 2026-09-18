#!/usr/bin/env python3
"""無 psql 主機用 Docker runner 的命令組裝測試。"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
RUNNER = REPO / "data_pipeline" / "runner" / "run.sh"


class RunnerTests(unittest.TestCase):
    def test_builds_missing_image_and_runs_script_with_repo_mount(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            env_file = temp / "pipeline.env"
            env_file.write_text("DATABASE_URL=postgresql://supabase-db:5432/postgres\n")
            docker_log = temp / "docker.log"
            fake_docker = temp / "docker"
            fake_docker.write_text(
                "#!/usr/bin/env bash\n"
                'printf \'%s\\n\' "$*" >> "$DOCKER_LOG"\n'
                'if [ "${1:-}" = image ] && [ "${2:-}" = inspect ]; then exit 1; fi\n'
                "exit 0\n",
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            env = {
                **os.environ,
                "PATH": f"{temp}:{os.environ['PATH']}",
                "DOCKER_LOG": str(docker_log),
                "PIPELINE_IMAGE": "pipeline-test",
                "PIPELINE_NETWORK": "test-network",
            }
            proc = subprocess.run(
                [
                    "bash",
                    str(RUNNER),
                    "--env-file",
                    str(env_file),
                    "leak_probe.py",
                    "--help",
                ],
                cwd=REPO,
                env=env,
                text=True,
                capture_output=True,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            commands = docker_log.read_text(encoding="utf-8")
            self.assertIn("image inspect pipeline-test", commands)
            self.assertIn("build -t pipeline-test", commands)
            self.assertIn("run --rm --network test-network", commands)
            self.assertIn(f"-v {REPO}:/work", commands)
            self.assertIn(
                "-w /work/data_pipeline/.agents/skills/scam-knowledge-pipeline/scripts",
                commands,
            )
            self.assertIn(f"--env-file {env_file}", commands)
            self.assertIn("pipeline-test python3 leak_probe.py --help", commands)


if __name__ == "__main__":
    unittest.main()
