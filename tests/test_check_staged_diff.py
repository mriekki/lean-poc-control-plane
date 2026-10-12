import unittest

from tools.check_staged_diff import filter_diff_check_output


class FilterDiffCheckOutputTests(unittest.TestCase):
    def test_allows_markdown_trailing_whitespace(self):
        output = (
            "docs/product/PRODUCT_BRIEF.md:3: trailing whitespace.\n"
            "+Status: **Approved**  \n"
        )

        errors, ignored = filter_diff_check_output(output)

        self.assertEqual([], errors)
        self.assertEqual(2, len(ignored))

    def test_rejects_non_markdown_trailing_whitespace(self):
        output = "tools/example.py:3: trailing whitespace.\n+value = 1  \n"

        errors, ignored = filter_diff_check_output(output)

        self.assertEqual([], ignored)
        self.assertEqual(2, len(errors))

    def test_rejects_other_markdown_whitespace_errors(self):
        output = "README.md:7: space before tab in indent.\n+ \titem\n"

        errors, ignored = filter_diff_check_output(output)

        self.assertEqual([], ignored)
        self.assertEqual(2, len(errors))

    def test_allows_markdown_only_and_preserves_mixed_errors(self):
        output = (
            "docs/a.md:2: trailing whitespace.\n"
            "+line  \n"
            "config/settings.json:4: trailing whitespace.\n"
            "+  \"enabled\": true  \n"
        )

        errors, ignored = filter_diff_check_output(output)

        self.assertEqual(2, len(ignored))
        self.assertEqual(
            [
                "config/settings.json:4: trailing whitespace.",
                '+  "enabled": true  ',
            ],
            errors,
        )


if __name__ == "__main__":
    unittest.main()
