# Fix shade mismatch in p5
with open("tests/test_phase5_retailer_integrations_and_deals.py", "r", encoding="utf-8") as f:
    t = f.read()

t = t.replace(
    "assert result.match_classification in (MatchClassification.SIZE_VARIANT, MatchClassification.INCOMPATIBLE_MISMATCH)\n    assert not result.is_comparable\n    assert not result.shade_match",
    "assert result.match_classification in (MatchClassification.SHADE_VARIANT, MatchClassification.INCOMPATIBLE_MISMATCH)\n    assert not result.is_comparable\n    assert not result.shade_match"
)

t = t.replace(
    "assert result.match_classification in (MatchClassification.SIZE_VARIANT, MatchClassification.INCOMPATIBLE_MISMATCH)\n    assert not result.is_comparable\n    assert not result.formulation_match",
    "assert result.match_classification in (MatchClassification.FORMULATION_VARIANT, MatchClassification.INCOMPATIBLE_MISMATCH)\n    assert not result.is_comparable\n    assert not result.formulation_match"
)

with open("tests/test_phase5_retailer_integrations_and_deals.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(t)
print("Updated p5 tests.")

# Fix p6 test
with open("tests/test_phase6_live_price_engine.py", "r", encoding="utf-8") as f:
    t6 = f.read()

old_p6 = """        self.assertTrue(match.is_mismatch)
        self.assertFalse(match.is_comparable)
        self.assertIn(match.match_classification, (MatchClassification.SIZE_VARIANT, MatchClassification.INCOMPATIBLE_MISMATCH))"""

new_p6 = """        self.assertFalse(match.size_match)
        self.assertFalse(match.is_comparable)
        self.assertIn(match.match_classification, (MatchClassification.SIZE_VARIANT, MatchClassification.INCOMPATIBLE_MISMATCH))"""

t6 = t6.replace(old_p6, new_p6)
with open("tests/test_phase6_live_price_engine.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(t6)
print("Updated p6 test.")
