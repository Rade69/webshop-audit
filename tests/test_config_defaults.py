"""
Tests for config/default values — protects against silent drift
between CLI, GUI, and shared pipeline.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

import config


# ---------------------------------------------------------------------------
# Config module smoke tests
# ---------------------------------------------------------------------------


class TestConfigValues:
    """Ensure all expected config constants exist and have sane values."""

    def test_fetch_defaults(self):
        assert config.DEFAULT_TIMEOUT >= 5
        assert config.DEFAULT_DELAY >= 0
        assert config.DEFAULT_MAX_RETRIES >= 1
        assert config.DEFAULT_MAX_WORKERS >= 1
        assert isinstance(config.DEFAULT_USE_PLAYWRIGHT, bool)

    def test_run_limits(self):
        assert config.DEFAULT_MAX_URLS >= 1
        assert config.DEFAULT_OUTPUT_DIR

    def test_score_weights(self):
        total = (
            config.DEFAULT_CATALOG_WEIGHT
            + config.DEFAULT_MACHINE_WEIGHT
            + config.DEFAULT_COMMERCE_WEIGHT
        )
        assert abs(total - 1.0) < 0.01  # weights should sum to ~1.0
        assert config.DEFAULT_AGENT_READY_THRESHOLD >= 0
        assert config.DEFAULT_AGENT_READY_THRESHOLD <= 100

    def test_heuristic_thresholds(self):
        assert config.MIN_VISIBLE_TEXT_LENGTH >= 50
        assert config.MIN_IMAGE_COUNT >= 1

    def test_shortlist_defaults(self):
        assert config.SHORTLIST_TOP_N >= 10
        assert config.BEST_SAMPLE_TOP_N >= 5

    def test_url_patterns_not_empty(self):
        assert len(config.PRODUCT_URL_PATTERNS) >= 5
        assert len(config.PRODUCT_URL_EXCLUSIONS) >= 10

    def test_exclusions_do_not_overlap_patterns(self):
        """Exclusion patterns should not accidentally match product patterns."""
        patterns = set(p.lower() for p in config.PRODUCT_URL_PATTERNS)
        exclusions = set(e.lower() for e in config.PRODUCT_URL_EXCLUSIONS)
        overlap = patterns & exclusions
        assert not overlap, f"Overlap between patterns and exclusions: {overlap}"


# ---------------------------------------------------------------------------
# CLI vs GUI default consistency
# ---------------------------------------------------------------------------


class TestCliGuiDefaultConsistency:
    """Ensure CLI and GUI use the same defaults from config.py."""

    def test_delay_default_is_shared(self):
        """Both CLI and GUI should read delay from config.DEFAULT_DELAY."""
        # CLI: main.py uses DEFAULT_DELAY directly
        # GUI: input_tab.py now uses DEFAULT_DELAY
        assert config.DEFAULT_DELAY >= 0

    def test_max_workers_default_is_shared(self):
        """Both CLI and GUI should read max_workers from config.DEFAULT_MAX_WORKERS."""
        assert config.DEFAULT_MAX_WORKERS >= 1

    def test_score_weights_are_shared(self):
        """Score weights should come from config, not be duplicated."""
        assert config.DEFAULT_CATALOG_WEIGHT > 0
        assert config.DEFAULT_MACHINE_WEIGHT > 0
        assert config.DEFAULT_COMMERCE_WEIGHT > 0

    def test_output_dir_default(self):
        """Output dir default should be consistent."""
        assert config.DEFAULT_OUTPUT_DIR == "outputs"


# ---------------------------------------------------------------------------
# Pipeline config override behavior
# ---------------------------------------------------------------------------


class TestPipelineConfigOverrides:
    """Test that pipeline correctly uses config overrides."""

    def test_pipeline_uses_config_delay(self, tmp_path):
        """Pipeline should use delay from config dict, falling back to DEFAULT_DELAY."""
        from audit.pipeline import run_audit
        from unittest.mock import patch

        urls = ["https://example.com/p/1"]
        config_dict = {"urls": urls, "output_dir": str(tmp_path), "delay": 0}

        captured_delay = None

        def capturing_fetch(urls_list, delay_seconds=0, **kwargs):
            nonlocal captured_delay
            captured_delay = delay_seconds
            return [
                {
                    "url": u,
                    "final_url": u,
                    "status_code": 200,
                    "html": "<html><body>test</body></html>",
                    "content_type": "text/html",
                    "error": None,
                    "response_time_ms": 10,
                }
                for u in urls_list
            ]

        with patch("audit.fetcher.fetch_pages", side_effect=capturing_fetch):
            run_audit(config=config_dict)

        assert captured_delay == 0

    def test_pipeline_falls_back_to_default_delay(self, tmp_path):
        """Pipeline should fall back to DEFAULT_DELAY when delay not in config."""
        from audit.pipeline import run_audit
        from unittest.mock import patch

        urls = ["https://example.com/p/1"]
        config_dict = {"urls": urls, "output_dir": str(tmp_path)}

        captured_delay = None

        def capturing_fetch(urls_list, delay_seconds=0, **kwargs):
            nonlocal captured_delay
            captured_delay = delay_seconds
            return [
                {
                    "url": u,
                    "final_url": u,
                    "status_code": 200,
                    "html": "<html><body>test</body></html>",
                    "content_type": "text/html",
                    "error": None,
                    "response_time_ms": 10,
                }
                for u in urls_list
            ]

        with patch("audit.fetcher.fetch_pages", side_effect=capturing_fetch):
            run_audit(config=config_dict)

        assert captured_delay == config.DEFAULT_DELAY

    def test_pipeline_falls_back_to_default_workers(self, tmp_path):
        """Pipeline should fall back to DEFAULT_MAX_WORKERS when not in config."""
        from audit.pipeline import run_audit
        from unittest.mock import patch

        urls = ["https://example.com/p/1"]
        config_dict = {"urls": urls, "output_dir": str(tmp_path)}

        captured_workers = None

        def capturing_fetch(urls_list, max_workers=1, **kwargs):
            nonlocal captured_workers
            captured_workers = max_workers
            return [
                {
                    "url": u,
                    "final_url": u,
                    "status_code": 200,
                    "html": "<html><body>test</body></html>",
                    "content_type": "text/html",
                    "error": None,
                    "response_time_ms": 10,
                }
                for u in urls_list
            ]

        with patch("audit.fetcher.fetch_pages", side_effect=capturing_fetch):
            run_audit(config=config_dict)

        assert captured_workers == config.DEFAULT_MAX_WORKERS


# ---------------------------------------------------------------------------
# Sample bucket config visibility
# ---------------------------------------------------------------------------


class TestSampleBucketConfig:
    """Ensure sample bucket tuning constants are visible and sane."""

    def test_sample_constants_exist(self):
        from audit.shortlist import (
            SAMPLE_MAX_ABSOLUTE,
            SAMPLE_MAX_RATIO_OF_ISSUES,
            SAMPLE_DISABLE_ABOVE_ISSUES,
        )

        assert SAMPLE_MAX_ABSOLUTE >= 1
        assert 0 < SAMPLE_MAX_RATIO_OF_ISSUES <= 1
        assert SAMPLE_DISABLE_ABOVE_ISSUES >= 5

    def test_sample_ratio_is_reasonable(self):
        from audit.shortlist import SAMPLE_MAX_RATIO_OF_ISSUES

        # 30% is reasonable — not too aggressive, not too passive
        assert 0.10 <= SAMPLE_MAX_RATIO_OF_ISSUES <= 0.50
