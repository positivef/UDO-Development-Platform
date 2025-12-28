"""
Integration test for Version History API

Tests the Git integration service and version history endpoints.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.git_service import GitService
from app.models.version_history import VersionCommit, VersionHistory


def test_git_service():
    """Test Git service with current repository"""
    print("=" * 60)
    print("Testing Git Service")
    print("=" * 60)

    # Get current repository path
    repo_path = Path(__file__).parent.parent

    try:
        git_service = GitService(str(repo_path))
        print(f"[OK] Git service initialized for: {repo_path}")

        # Test: Get current branch
        current_branch = git_service.get_current_branch()
        assert isinstance(current_branch, str) and current_branch, "Branch should be a non-empty string"
        print(f"[OK] Current branch: {current_branch}")

        # Test: Get commit count
        total_commits = git_service.get_commit_count()
        assert isinstance(total_commits, int) and total_commits >= 0, "Total commits should be non-negative int"
        print(f"[OK] Total commits: {total_commits}")

        # Test: Get recent commits
        commits = git_service.get_commits(limit=5)
        assert isinstance(commits, list), "Commits should be a list"
        print(f"[OK] Fetched {len(commits)} recent commits")

        for i, commit in enumerate(commits, 1):
            print(f"\n  Commit {i}:")
            print(f"    Hash: {commit.short_hash}")
            print(f"    Author: {commit.author}")
            print(f"    Date: {commit.date}")
            print(f"    Message: {commit.message[:50]}...")
            print(f"    Files: {len(commit.files_modified)} modified, {commit.lines_added}+ {commit.lines_deleted}-")

        # Test: Get version history
        history = git_service.get_version_history(limit=10)
        print(f"\n[OK] Version history:")
        print(f"    Project: {history.project_name}")
        print(f"    Branch: {history.current_branch}")
        print(f"    Total commits: {history.total_commits}")
        print(f"    Contributors: {history.total_contributors}")

        # Test: Compare commits (if we have at least 2 commits)
        if len(commits) >= 2:
            comparison = git_service.compare_commits(commits[1].commit_hash, commits[0].commit_hash)
            assert comparison.files_changed is not None, "Comparison should include files_changed"
            print(f"\n[OK] Commit comparison:")
            print(f"    From: {comparison.from_commit}")
            print(f"    To: {comparison.to_commit}")
            print(f"    Files changed: {len(comparison.files_changed)}")
            print(f"    Lines: +{comparison.total_lines_added} -{comparison.total_lines_deleted}")

        print("\n" + "=" * 60)
        print("[OK] All Git service tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback

        traceback.print_exc()
        raise


def test_api_models():
    """Test data models"""
    print("\n" + "=" * 60)
    print("Testing Data Models")
    print("=" * 60)

    try:
        from datetime import datetime

        # Test VersionCommit model
        commit = VersionCommit(
            commit_hash="a" * 40,
            short_hash="a" * 7,
            author="Test Author",
            author_email="test@example.com",
            date=datetime.now(),
            message="Test commit",
            files_modified=["file1.py", "file2.py"],
            files_added=["file3.py"],
            files_deleted=[],
            lines_added=100,
            lines_deleted=50,
            tags=["v1.0.0"],
            branches=["main"],
        )
        assert commit.short_hash == "a" * 7
        assert commit.lines_added == 100

        # Test VersionHistory model
        history = VersionHistory(
            project_name="Test Project",
            project_path="/path/to/project",
            current_branch="main",
            total_commits=150,
            commits=[commit],
            total_contributors=5,
            first_commit_date=datetime.now(),
            last_commit_date=datetime.now(),
        )
        assert history.total_commits == 150
        assert history.commits[0].commit_hash == commit.commit_hash

        print("\n" + "=" * 60)
        print("[OK] All model tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] Model test failed: {e}")
        import traceback

        traceback.print_exc()
        raise


def main():
    """Run all tests"""
    print("\n[TEST] Version History API Integration Tests\n")

    results = []

    # Run tests
    results.append(("Data Models", test_api_models()))
    results.append(("Git Service", test_git_service()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n[SUCCESS] All tests passed successfully!")
        return 0
    else:
        print("\n[FAILED] Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
