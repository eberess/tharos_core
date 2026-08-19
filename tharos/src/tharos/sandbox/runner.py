"""Exécution automatisée des tests dans une sandbox Docker."""

import io
import tarfile
from dataclasses import dataclass, field

import docker
from docker.models.containers import Container


SANDBOX_IMAGE = "tharos-sandbox:latest"
SANDBOX_TIMEOUT = 120
SANDBOX_WORKDIR = "/sandbox/run"


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

    @staticmethod
    def _build_archive(code_str: str, test_str: str) -> bytes:
        """Construit une archive tar (en mémoire) contenant le code et le test.

        Les fichiers sont placés sous ``run/`` pour être extraits dans le
        répertoire de travail de la sandbox sans dépendre d'un bind mount
        hôte (qui échoue quand l'orchestrateur tourne lui-même en conteneur).
        """
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as tar:
            run_dir = tarfile.TarInfo(name="run")
            run_dir.type = tarfile.DIRTYPE
            run_dir.mode = 0o755
            tar.addfile(run_dir)

            for name, content in (
                ("run/generated_code.py", code_str),
                ("run/test_generated.py", test_str),
            ):
                data = content.encode("utf-8")
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                info.mode = 0o644
                tar.addfile(info, io.BytesIO(data))
        buffer.seek(0)
        return buffer.read()

    def run_tests(self, code_str: str, test_str: str) -> SandboxResult:
        archive = self._build_archive(code_str, test_str)

        container: Container | None = None
        try:
            container = self._client.containers.create(
                self.image,
                command=[
                    "-v",
                    "--tb=short",
                    f"--rootdir={SANDBOX_WORKDIR}",
                    "--override-ini=addopts=",
                    "test_generated.py",
                ],
                working_dir=SANDBOX_WORKDIR,
                environment={"PYTHONPATH": SANDBOX_WORKDIR},
                network_mode="none",
                detach=True,
            )

            container.put_archive("/sandbox", archive)
            container.start()

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
