from __future__ import annotations

import unittest
from pathlib import Path


class GenerationBytecodeHygieneTests(unittest.TestCase):
    def test_generated_workspace_validation_redirects_python_bytecode(self) -> None:
        workflow = Path(".github/workflows/generate-project.yml").read_text(encoding="utf-8")
        self.assertIn("PYTHONPYCACHEPREFIX: ${{ runner.temp }}/project-forge-pycache", workflow)
        self.assertIn("python -m compileall -q \"$RUNNER_TEMP/generated/tools\"", workflow)

    def test_publication_fails_if_generated_tree_contains_python_cache_artifacts(self) -> None:
        workflow = Path(".github/workflows/generate-project.yml").read_text(encoding="utf-8")
        self.assertIn("-type f -name '*.pyc'", workflow)
        self.assertIn("-type d -name '__pycache__'", workflow)
        self.assertIn("validation caches must stay outside publication", workflow)


if __name__ == "__main__":
    unittest.main()
