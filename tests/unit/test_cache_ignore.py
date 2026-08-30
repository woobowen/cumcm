import subprocess


def test_upstream_cache_is_ignored(repo_root):
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".cache/upstream"], cwd=repo_root, check=False
    )
    assert result.returncode == 0
