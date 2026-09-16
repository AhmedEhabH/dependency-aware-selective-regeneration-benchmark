{
  "study_id": "real-commit-impact-v2-dev-inference",
  "gates": [
    {
      "gate": 1,
      "name": "Dataset Validation (V2 DEV)",
      "passed": true,
      "checks": [
        {
          "check": "v2_dev_count_150",
          "ok": true,
          "detail": 150
        },
        {
          "check": "roles_only_train_validation",
          "ok": true,
          "detail": [
            "DEV_TRAIN",
            "DEV_VALIDATION"
          ]
        },
        {
          "check": "no_legacy_exposed_in_v2",
          "ok": true,
          "detail": "no v1 exposed case in v2 dev"
        },
        {
          "check": "proxy_subset_universe_djangocms-rc-0168319ab703",
          "ok": true,
          "detail": []
        },
        {
          "check": "proxy_subset_universe_djangocms-rc-0224f1e364b0",
          "ok": true,
          "detail": []
        },
        {
          "check": "proxy_subset_universe_djangocms-rc-036991d6b9bf",
          "ok": true,
          "detail": []
        },
        {
          "check": "proxy_subset_universe_djangocms-rc-0526cdde8118",
          "ok": true,
          "detail": []
        },
        {
          "check": "proxy_subset_universe_djangocms-rc-0555c9b04025",
          "ok": true,
          "detail": []
        },
        {
          "check": "proxy_subset_universe_djangocms-rc-067460447d47",
          "ok": true,
          "detail": []
        },
        {
          "check": "test_reserve_never_in_dev",
          "ok": true,
          "detail": "none"
        }
      ]
    },
    {
      "gate": 2,
      "name": "Prompt Validation (V2 DEV)",
      "passed": true,
      "checks": [
        {
          "check": "no_hidden_marker_djangocms-rc-0168319ab703",
          "ok": true,
          "detail": []
        },
        {
          "check": "sparse_policy_djangocms-rc-0168319ab703",
          "ok": true,
          "detail": "ok"
        },
        {
          "check": "intent_present_djangocms-rc-0168319ab703",
          "ok": true,
          "detail": "fix edit strings"
        },
        {
          "check": "no_hidden_marker_djangocms-rc-0224f1e364b0",
          "ok": true,
          "detail": []
        },
        {
          "check": "sparse_policy_djangocms-rc-0224f1e364b0",
          "ok": true,
          "detail": "ok"
        },
        {
          "check": "intent_present_djangocms-rc-0224f1e364b0",
          "ok": true,
          "detail": "feat: Add `FrontendEditableAdminMixin` endpoint to plugins ("
        },
        {
          "check": "no_hidden_marker_djangocms-rc-036991d6b9bf",
          "ok": true,
          "detail": []
        },
        {
          "check": "sparse_policy_djangocms-rc-036991d6b9bf",
          "ok": true,
          "detail": "ok"
        },
        {
          "check": "intent_present_djangocms-rc-036991d6b9bf",
          "ok": true,
          "detail": "Fixes wizards with permissions"
        },
        {
          "check": "no_hidden_marker_djangocms-rc-0526cdde8118",
          "ok": true,
          "detail": []
        },
        {
          "check": "sparse_policy_djangocms-rc-0526cdde8118",
          "ok": true,
          "detail": "ok"
        },
        {
          "check": "intent_present_djangocms-rc-0526cdde8118",
          "ok": true,
          "detail": "fixes issue with page menu missing"
        },
        {
          "check": "no_hidden_marker_djangocms-rc-0555c9b04025",
          "ok": true,
          "detail": []
        },
        {
          "check": "sparse_policy_djangocms-rc-0555c9b04025",
          "ok": true,
          "detail": "ok"
        },
        {
          "check": "intent_present_djangocms-rc-0555c9b04025",
          "ok": true,
          "detail": "wrap loaded js files with pre and post"
        },
        {
          "check": "no_hidden_marker_djangocms-rc-067460447d47",
          "ok": true,
          "detail": []
        },
        {
          "check": "sparse_policy_djangocms-rc-067460447d47",
          "ok": true,
          "detail": "ok"
        },
        {
          "check": "intent_present_djangocms-rc-067460447d47",
          "ok": true,
          "detail": "Removed usages of site_id and parent_id"
        },
        {
          "check": "zero_model_calls_render",
          "ok": true,
          "detail": "string rendering only"
        }
      ]
    },
    {
      "gate": 3,
      "name": "Pipeline Smoke (V2 DEV)",
      "passed": true,
      "checks": [
        {
          "check": "mock_sparse_decode_valid",
          "ok": true,
          "detail": true
        },
        {
          "check": "zero_calls_smoke",
          "ok": true,
          "detail": "fixture only"
        }
      ]
    },
    {
      "gate": 4,
      "name": "Dry Run (V2 DEV)",
      "passed": true,
      "checks": [
        {
          "check": "cells_exactly_450",
          "ok": true,
          "detail": 450
        },
        {
          "check": "run_ids_unique",
          "ok": true,
          "detail": 450
        },
        {
          "check": "three_reps_each",
          "ok": true,
          "detail": "150x3=450"
        },
        {
          "check": "frozen_config",
          "ok": true,
          "detail": "qwen3-coder/deepinfra/temp0/cap16384"
        },
        {
          "check": "zero_calls_dryrun",
          "ok": true,
          "detail": "manifest shape only"
        }
      ]
    },
    {
      "gate": 5,
      "name": "Integration (V2 DEV)",
      "passed": true,
      "checks": [
        {
          "check": "manifest_sparse_only",
          "ok": true,
          "detail": "sparse_v2 only"
        },
        {
          "check": "manifest_protocol_frozen",
          "ok": true,
          "detail": "real-commit-p1-v1.0.0"
        },
        {
          "check": "row_shape",
          "ok": true,
          "detail": "7 fields"
        }
      ]
    },
    {
      "gate": 6,
      "name": "Metric Verification (V2 DEV)",
      "passed": true,
      "checks": [
        {
          "check": "micro_recomputed",
          "ok": true,
          "detail": {
            "tp": 3,
            "fp": 1,
            "fn": 0,
            "precision": 0.75,
            "recall": 1.0,
            "f1": 0.8571428571428571,
            "fnr": 0.0,
            "full_recall": true,
            "proxy_size": 3,
            "predicted_size": 4
          }
        },
        {
          "check": "empty_fail_closed",
          "ok": true,
          "detail": {
            "tp": 0,
            "fp": 0,
            "fn": 1,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "fnr": 1.0,
            "full_recall": false,
            "proxy_size": 1,
            "predicted_size": 0
          }
        }
      ]
    }
  ],
  "all_passed": true,
  "ran_at": "2026-09-16T12:40:01.069881+00:00"
}