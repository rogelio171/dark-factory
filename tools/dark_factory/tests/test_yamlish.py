import unittest

from dark_factory.yamlish import dump_simple_yaml, format_scalar, parse_scalar, parse_simple_yaml


class YamlishRoundTripTests(unittest.TestCase):
    def test_scalar_round_trip_is_stable(self) -> None:
        values = [
            'waiting on "auth: v2" rollout',
            "path C:\\Users\\dev\\app",
            'quotes "and" backslash \\ and colon:',
            "line one\nline two: with colon",
            "true",
            "false",
            "'single quoted'",
            "plain value",
            "",
        ]
        for value in values:
            with self.subTest(value=value):
                current = value
                for _ in range(3):
                    current = parse_scalar(format_scalar(current))
                self.assertEqual(current, value)

    def test_document_round_trip_is_stable(self) -> None:
        data = {
            "ticket": "OFRS2-1",
            "title": 'Fix "auth: v2" rollout',
            "blocked_reason": "line one\nline two",
            "auto_merge_eligible": False,
            "target_modules": ["apps/web", "libs: shared"],
            "validation_commands": {"lint": "npm run lint", "note": 'a "quoted": value'},
        }
        current = data
        for _ in range(3):
            current = parse_simple_yaml(dump_simple_yaml(current))
        self.assertEqual(current, data)


if __name__ == "__main__":
    unittest.main()
