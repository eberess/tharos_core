"""Tests unitaires pour le DockerSandboxRunner (mocké)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tharos.sandbox.runner import DockerSandboxRunner, SandboxResult, _rmtree


VALID_CODE = 'def add(a: int, b: int) -> int:\n    return a + b\n'
VALID_TEST = (
    "from generated_code import add\n\n"
    "def test_add():\n"
    "    assert add(2, 3) == 5\n"
)

FAILING_CODE = 'def add(a: int, b: int) -> int:\n    return a - b\n'
FAILING_TEST = (
    "from generated_code import add\n\n"
    "def test_add():\n"
    "    assert add(2, 3) == 5\n"
)


def _make_container_mock(exit_code: int, out_text: str, err_text: str) -> MagicMock:
    container = MagicMock()
    container.short_id = "abc1234"
    container.wait.return_value = {"StatusCode": exit_code}

    def _logs(stdout=True, stderr=True):
        if stdout and not stderr:
            return out_text.encode()
        if stderr and not stdout:
            return err_text.encode()
        return b""

    container.logs.side_effect = _logs
    container.remove.return_value = None
    return container


class TestDockerSandboxRunner:
    @patch("tharos.sandbox.runner.docker")
    def test_passing_code(self, mock_docker: MagicMock) -> None:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        container = _make_container_mock(0, "1 passed\n", "")
        mock_client.containers.run.return_value = container

        runner = DockerSandboxRunner(image="test:latest")
        result = runner.run_tests(VALID_CODE, VALID_TEST)

        assert result.passed is True
        assert result.exit_code == 0
        assert result.container_id == "abc1234"
        mock_client.containers.run.assert_called_once()

        call_kwargs = mock_client.containers.run.call_args
        assert call_kwargs.kwargs["network_mode"] == "none"

    @patch("tharos.sandbox.runner.docker")
    def test_failing_code(self, mock_docker: MagicMock) -> None:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        container = _make_container_mock(
            1,
            "FAILED tests/test_generated.py::test_add\n",
            "AssertionError: assert False\n",
        )
        mock_client.containers.run.return_value = container

        runner = DockerSandboxRunner(image="test:latest")
        result = runner.run_tests(FAILING_CODE, FAILING_TEST)

        assert result.passed is False
        assert result.exit_code == 1
        assert "AssertionError" in result.stderr or "FAILED" in result.stdout

    @patch("tharos.sandbox.runner.docker")
    def test_coverage_extracted(self, mock_docker: MagicMock) -> None:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        stdout = "1 passed\nTOTAL                    10      2    80%"
        container = _make_container_mock(0, stdout, "")
        mock_client.containers.run.return_value = container

        runner = DockerSandboxRunner()
        result = runner.run_tests(VALID_CODE, VALID_TEST)

        assert "TOTAL" in result.coverage
        assert "80%" in result.coverage

    @patch("tharos.sandbox.runner.docker")
    def test_container_removed(self, mock_docker: MagicMock) -> None:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        container = _make_container_mock(0, "passed", "")
        mock_client.containers.run.return_value = container

        runner = DockerSandboxRunner()
        runner.run_tests(VALID_CODE, VALID_TEST)

        container.remove.assert_called_once_with(force=True)

    @patch("tharos.sandbox.runner.docker")
    def test_volume_mount(self, mock_docker: MagicMock) -> None:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        container = _make_container_mock(0, "1 passed", "")
        mock_client.containers.run.return_value = container

        runner = DockerSandboxRunner()
        runner.run_tests(VALID_CODE, VALID_TEST)

        call_kwargs = mock_client.containers.run.call_args
        volumes = call_kwargs.kwargs.get("volumes", {})
        assert len(volumes) == 1

        mount_path = list(volumes.keys())[0]
        assert Path(mount_path).exists() is False


class TestRmtree:
    def test_removes_existing_dir(self, tmp_path: Path) -> None:
        d = tmp_path / "to_remove"
        d.mkdir()
        (d / "file.txt").write_text("hello")
        _rmtree(d)
        assert not d.exists()

    def test_removes_nonexistent_dir(self, tmp_path: Path) -> None:
        d = tmp_path / "nope"
        _rmtree(d)
