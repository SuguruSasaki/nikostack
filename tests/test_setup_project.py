"""Setup must preserve existing labels and never trigger issues."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "setup", ROOT / "skills/nikostack/scripts/setup-project.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class LabelSetup(unittest.TestCase):
    def setUp(self):
        self.definitions = json.loads(
            (ROOT / "skills/nikostack/assets/issue-labels.json").read_text())
        self.labels = [{"name": "AI-READY", "color": "abcdef",
                        "description": "Preserve the project definition"}]
        self.original = copy.deepcopy(self.labels)
        self.requests = []

    def api(self, method, path, payload=None, **kwargs):
        self.requests.append((method, path))
        if method == "POST":
            self.labels.append(copy.deepcopy(payload))
            return payload
        if "/labels?" in path:
            return [copy.deepcopy(self.labels)]
        return {"has_issues": True, "full_name": "example/product",
                "permissions": {"push": True}}

    def test_preview_never_mutates(self):
        result = setup.prepare("example/product", self.definitions, request=self.api)
        self.assertEqual(len(result["missing"]), 3)
        self.assertEqual(self.labels, self.original)
        self.assertTrue(all(method == "GET" for method, _ in self.requests))

    def test_apply_adds_only_missing_and_can_be_repeated(self):
        first = setup.prepare("example/product", self.definitions, True, self.api)
        second = setup.prepare("example/product", self.definitions, True, self.api)
        self.assertEqual(len(first["created"]), 3)
        self.assertEqual(second["created"], [])
        self.assertEqual(self.labels[0], self.original[0])
        self.assertFalse(any(method in ("PUT", "PATCH", "DELETE")
                             for method, _ in self.requests))
        self.assertFalse(any("/issues/" in path for _, path in self.requests))

    def test_disabled_issues_fail_before_mutation(self):
        with self.assertRaises(setup.SetupError):
            setup.prepare("example/product", self.definitions, True,
                          lambda *a, **k: {"has_issues": False})

    def test_readonly_access_cannot_create_labels(self):
        def read_only(method, path, *args, **kwargs):
            return [[]] if "/labels?" in path else {
                "has_issues": True, "full_name": "example/product", "permissions": {}}
        with self.assertRaises(setup.SetupError):
            setup.prepare("example/product", self.definitions, True, read_only)

    def test_invalid_repository_does_not_make_requests(self):
        with self.assertRaises(setup.SetupError):
            setup.prepare("example/product; bad", self.definitions, True, self.api)
        self.assertEqual(self.requests, [])


if __name__ == "__main__":
    unittest.main()
