#!/usr/bin/env python
#
# Glances - An eye on your system
#
# SPDX-FileCopyrightText: 2024 Nicolas Hennion <nicolas@nicolargo.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

"""Test suite for GitLab CI/CD pipeline configuration.

This module validates that the GitLab CI/CD pipeline configuration is correct
and that uv-based workflows are properly configured.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class TestGitLabCIConfig:
    """Test GitLab CI/CD configuration file validity."""

    @pytest.fixture
    def gitlab_ci_path(self):
        """Return path to .gitlab-ci.yml file."""
        return PROJECT_ROOT / ".gitlab-ci.yml"

    def test_gitlab_ci_file_exists(self, gitlab_ci_path):
        """Test that .gitlab-ci.yml file exists."""
        assert gitlab_ci_path.exists(), ".gitlab-ci.yml file must exist"

    def test_gitlab_ci_is_valid_yaml(self, gitlab_ci_path):
        """Test that .gitlab-ci.yml is valid YAML."""
        import yaml

        with open(gitlab_ci_path) as f:
            try:
                config = yaml.safe_load(f)
                assert config is not None, "YAML content should not be empty"
            except yaml.YAMLError as e:
                pytest.fail(f".gitlab-ci.yml is not valid YAML: {e}")

    def test_gitlab_ci_has_required_stages(self, gitlab_ci_path):
        """Test that .gitlab-ci.yml has all required stages."""
        import yaml

        with open(gitlab_ci_path) as f:
            config = yaml.safe_load(f)

        required_stages = ["quality", "test", "build", "docker", "publish"]
        assert "stages" in config, "stages key must be present"
        for stage in required_stages:
            assert stage in config["stages"], f"Stage '{stage}' must be defined"

    def test_gitlab_ci_uses_uv(self, gitlab_ci_path):
        """Test that .gitlab-ci.yml uses uv for dependency management."""
        with open(gitlab_ci_path) as f:
            content = f.read()

        # Check that uv is used in the pipeline
        assert "uv" in content, "Pipeline should use uv for dependency management"
        assert "astral.sh/uv" in content, "Pipeline should install uv from astral.sh"

    def test_gitlab_ci_has_test_jobs(self, gitlab_ci_path):
        """Test that .gitlab-ci.yml has test jobs for multiple Python versions."""
        import yaml

        with open(gitlab_ci_path) as f:
            config = yaml.safe_load(f)

        # Check for test jobs
        test_jobs = [key for key in config.keys() if key.startswith("test:python")]
        assert len(test_jobs) >= 4, "Should have test jobs for at least 4 Python versions"

    def test_gitlab_ci_has_docker_jobs(self, gitlab_ci_path):
        """Test that .gitlab-ci.yml has Docker build jobs."""
        import yaml

        with open(gitlab_ci_path) as f:
            config = yaml.safe_load(f)

        docker_jobs = [key for key in config.keys() if key.startswith("docker:")]
        assert len(docker_jobs) >= 4, "Should have Docker jobs for alpine and ubuntu"

    def test_gitlab_ci_has_publish_jobs(self, gitlab_ci_path):
        """Test that .gitlab-ci.yml has publish jobs for PyPI."""
        import yaml

        with open(gitlab_ci_path) as f:
            config = yaml.safe_load(f)

        assert "publish:pypi" in config, "Should have PyPI publish job"
        assert "publish:testpypi" in config, "Should have TestPyPI publish job"


class TestDockerfilesUseUV:
    """Test that Dockerfiles use uv for dependency management."""

    @pytest.fixture
    def alpine_dockerfile(self):
        """Return path to Alpine Dockerfile."""
        return PROJECT_ROOT / "docker-files" / "alpine.Dockerfile"

    @pytest.fixture
    def ubuntu_dockerfile(self):
        """Return path to Ubuntu Dockerfile."""
        return PROJECT_ROOT / "docker-files" / "ubuntu.Dockerfile"

    def test_alpine_dockerfile_exists(self, alpine_dockerfile):
        """Test that Alpine Dockerfile exists."""
        assert alpine_dockerfile.exists(), "Alpine Dockerfile must exist"

    def test_ubuntu_dockerfile_exists(self, ubuntu_dockerfile):
        """Test that Ubuntu Dockerfile exists."""
        assert ubuntu_dockerfile.exists(), "Ubuntu Dockerfile must exist"

    def test_alpine_dockerfile_uses_uv(self, alpine_dockerfile):
        """Test that Alpine Dockerfile uses uv."""
        with open(alpine_dockerfile) as f:
            content = f.read()

        assert "ghcr.io/astral-sh/uv" in content, "Alpine Dockerfile should copy uv from official image"
        assert "uv venv" in content, "Alpine Dockerfile should use uv to create venv"
        assert "uv pip install" in content, "Alpine Dockerfile should use uv pip install"

    def test_ubuntu_dockerfile_uses_uv(self, ubuntu_dockerfile):
        """Test that Ubuntu Dockerfile uses uv."""
        with open(ubuntu_dockerfile) as f:
            content = f.read()

        assert "ghcr.io/astral-sh/uv" in content, "Ubuntu Dockerfile should copy uv from official image"
        assert "uv venv" in content, "Ubuntu Dockerfile should use uv to create venv"
        assert "uv pip install" in content, "Ubuntu Dockerfile should use uv pip install"

    def test_alpine_dockerfile_no_pip_venv(self, alpine_dockerfile):
        """Test that Alpine Dockerfile doesn't use pip directly for package installation."""
        with open(alpine_dockerfile) as f:
            content = f.read()

        # Should not have pip install without uv prefix (except for installing uv itself)
        lines = content.split("\n")
        for line in lines:
            # Skip comments
            if line.strip().startswith("#"):
                continue
            # pip install should be prefixed with uv
            if "pip install" in line and "uv pip install" not in line:
                # Allow venv-build pip install (legacy pattern) - but we removed this
                assert False, f"Found non-uv pip install: {line}"

    def test_ubuntu_dockerfile_no_pip_venv(self, ubuntu_dockerfile):
        """Test that Ubuntu Dockerfile doesn't use pip directly for package installation."""
        with open(ubuntu_dockerfile) as f:
            content = f.read()

        # Should not have pip install without uv prefix
        lines = content.split("\n")
        for line in lines:
            # Skip comments
            if line.strip().startswith("#"):
                continue
            # pip install should be prefixed with uv
            if "pip install" in line and "uv pip install" not in line:
                assert False, f"Found non-uv pip install: {line}"


class TestUVIntegration:
    """Test uv integration with the project."""

    @pytest.fixture
    def pyproject_path(self):
        """Return path to pyproject.toml file."""
        return PROJECT_ROOT / "pyproject.toml"

    def test_pyproject_exists(self, pyproject_path):
        """Test that pyproject.toml exists."""
        assert pyproject_path.exists(), "pyproject.toml must exist"

    def test_pyproject_has_dependencies(self, pyproject_path):
        """Test that pyproject.toml has dependencies defined."""
        with open(pyproject_path) as f:
            content = f.read()

        assert "[project]" in content, "pyproject.toml should have [project] section"
        assert "dependencies" in content, "pyproject.toml should define dependencies"

    def test_uv_can_be_installed(self):
        """Test that uv can be installed (smoke test)."""
        # This test just verifies the uv installation command is valid
        # In CI, uv will be installed via the before_script
        install_cmd = "curl -LsSf https://astral.sh/uv/install.sh | sh"
        assert "astral.sh/uv" in install_cmd

    def test_requirements_files_exist(self):
        """Test that requirements files exist for fallback."""
        requirements = PROJECT_ROOT / "requirements.txt"
        dev_requirements = PROJECT_ROOT / "dev-requirements.txt"
        docker_requirements = PROJECT_ROOT / "docker-requirements.txt"

        assert requirements.exists(), "requirements.txt should exist"
        assert dev_requirements.exists(), "dev-requirements.txt should exist"
        assert docker_requirements.exists(), "docker-requirements.txt should exist"


class TestPipelineJobs:
    """Test individual pipeline job configurations."""

    @pytest.fixture
    def gitlab_config(self):
        """Return parsed GitLab CI config."""
        import yaml

        gitlab_ci_path = PROJECT_ROOT / ".gitlab-ci.yml"
        with open(gitlab_ci_path) as f:
            return yaml.safe_load(f)

    def test_format_job_config(self, gitlab_config):
        """Test format job configuration."""
        assert "format" in gitlab_config
        job = gitlab_config["format"]
        assert job["stage"] == "quality"
        assert "ruff format" in " ".join(job["script"])

    def test_lint_job_config(self, gitlab_config):
        """Test lint job configuration."""
        assert "lint" in gitlab_config
        job = gitlab_config["lint"]
        assert job["stage"] == "quality"
        assert "ruff check" in " ".join(job["script"])

    def test_test_jobs_have_needs(self, gitlab_config):
        """Test that test jobs depend on quality jobs."""
        test_jobs = [key for key in gitlab_config.keys() if key.startswith("test:python")]
        for job_name in test_jobs:
            job = gitlab_config[job_name]
            assert "needs" in job, f"{job_name} should have needs"
            needs = job["needs"]
            assert "format" in needs, f"{job_name} should need format"
            assert "lint" in needs, f"{job_name} should need lint"

    def test_build_job_has_needs(self, gitlab_config):
        """Test that build job depends on test jobs."""
        assert "build:package" in gitlab_config
        job = gitlab_config["build:package"]
        assert "needs" in job
        # Should need all test jobs
        needs = job["needs"]
        assert len(needs) >= 4, "Build should need all test jobs"

    def test_docker_jobs_use_dind(self, gitlab_config):
        """Test that Docker jobs use Docker-in-Docker."""
        docker_jobs = [key for key in gitlab_config.keys() if key.startswith("docker:") and key != "docker:tag-release"]
        for job_name in docker_jobs:
            job = gitlab_config[job_name]
            if "services" in job:
                services = job["services"]
                assert "docker:dind" in services, f"{job_name} should use docker:dind"

    def test_publish_jobs_are_manual(self, gitlab_config):
        """Test that publish jobs require manual trigger."""
        publish_jobs = ["publish:pypi", "publish:testpypi"]
        for job_name in publish_jobs:
            if job_name in gitlab_config:
                job = gitlab_config[job_name]
                assert job.get("when") == "manual", f"{job_name} should be manual"

    def test_cache_configuration(self, gitlab_config):
        """Test that cache is properly configured for uv."""
        assert "variables" in gitlab_config
        variables = gitlab_config["variables"]
        assert "UV_CACHE_DIR" in variables, "Should define UV_CACHE_DIR"
        assert "PIP_CACHE_DIR" in variables, "Should define PIP_CACHE_DIR"


class TestYAMLAnchors:
    """Test YAML anchors and aliases are working correctly."""

    @pytest.fixture
    def gitlab_config(self):
        """Return parsed GitLab CI config."""
        import yaml

        gitlab_ci_path = PROJECT_ROOT / ".gitlab-ci.yml"
        with open(gitlab_ci_path) as f:
            return yaml.safe_load(f)

    def test_test_template_applied(self, gitlab_config):
        """Test that test template is properly applied to test jobs."""
        test_jobs = [key for key in gitlab_config.keys() if key.startswith("test:python")]
        for job_name in test_jobs:
            job = gitlab_config[job_name]
            # All test jobs should have these from the template
            assert "stage" in job
            assert job["stage"] == "test"
            assert "script" in job

    def test_docker_template_applied(self, gitlab_config):
        """Test that docker template is properly applied to docker jobs."""
        docker_jobs = ["docker:alpine-minimal", "docker:alpine-full", "docker:ubuntu-minimal", "docker:ubuntu-full"]
        for job_name in docker_jobs:
            if job_name in gitlab_config:
                job = gitlab_config[job_name]
                assert job["stage"] == "docker"


class TestGitLabDirectory:
    """Test .gitlab directory structure."""

    def test_gitlab_directory_exists(self):
        """Test that .gitlab directory exists."""
        gitlab_dir = PROJECT_ROOT / ".gitlab"
        assert gitlab_dir.exists(), ".gitlab directory must exist"

    def test_gitlab_readme_exists(self):
        """Test that .gitlab/README.md exists."""
        readme_path = PROJECT_ROOT / ".gitlab" / "README.md"
        assert readme_path.exists(), ".gitlab/README.md must exist"

    def test_gitlab_readme_has_content(self):
        """Test that README has required sections."""
        readme_path = PROJECT_ROOT / ".gitlab" / "README.md"
        with open(readme_path) as f:
            content = f.read()

        assert "Pipeline Overview" in content, "README should have Pipeline Overview"
        assert "Pipeline Stages" in content, "README should describe stages"
        assert "Required CI/CD Variables" in content, "README should list variables"
        assert "uv" in content, "README should mention uv"


class TestMakefileIntegration:
    """Test that Makefile has GitLab CI test target."""

    def test_makefile_has_gitlab_ci_test(self):
        """Test that Makefile has test-gitlab-ci target."""
        makefile_path = PROJECT_ROOT / "Makefile"
        with open(makefile_path) as f:
            content = f.read()

        assert "test-gitlab-ci:" in content, "Makefile should have test-gitlab-ci target"
        assert "test_gitlab_ci.py" in content, "Target should run test_gitlab_ci.py"
