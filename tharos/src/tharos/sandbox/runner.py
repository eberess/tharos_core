"""Exécution automatisée des tests dans une sandbox Docker."""

import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import docker
from docker.models.containers import Container


SANDBOX_IMAGE = "tharos-sandbox:latest"
SANDBOX_TIMEOUT = 120


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    passed: bool
    coverage: str = ""
    container_id: str = ""


class DockerSandboxRunner:
    """Exécute du code généré + tests pytest dans un conteneur Docker isolé."""

    def __init__(
        self,
        image: str = SANDBOX_IMAGE,
        timeout: int = SANDBOX_TIMEOUT,
    ) -> None:
        self.image = image
        self.timeout = timeout
        self._client = docker.from_env()

    def run_tests(self, code_str: str, test_str: str) -> SandboxResult:
        work_dir = Path(tempfile.mkdtemp(prefix="tharos_sandbox_"))

        module_name = "generated_code"
        code_file = work_dir / f"{module_name}.py"
        test_file = work_dir / "test_generated.py"

        code_file.write_text(code_str, encoding="utf-8")
        test_file.write_text(test_str, encoding="utf-8")

        container: Container | None = None
        try:
            container = self._client.containers.run(
                self.image,
                command=["-v", "--tb=short", "--rootdir=/sandbox/run",
                         "--override-ini=addopts=", "test_generated.py"],
                volumes={str(work_dir): {"bind": "/sandbox/run", "mode": "rw"}},
                working_dir="/sandbox/run",
                environment={"PYTHONPATH": "/sandbox/run"},
                network_mode="none",
                detach=True,
                remove=False,
            )

            result = container.wait(timeout=self.timeout)
            exit_code = result.get("StatusCode", 1)

            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            coverage = ""
            for line in stdout.splitlines():
                if "TOTAL" in line and "%" in line:
                    coverage = line.strip()
                    break

            return SandboxResult(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                passed=(exit_code == 0),
                coverage=coverage,
                container_id=container.short_id,
            )

        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            _rmtree(work_dir)


def _rmtree(path: Path) -> None:
    import shutil
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
