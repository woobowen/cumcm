import json

from cumcm_skill_lab.eval.trace_summary import sanitize_error, summarize_jsonl


def test_trace_summary_counts_events_commands_and_usage():
    events = "\n".join(
        [
            json.dumps({"type": "started"}),
            json.dumps(
                {
                    "type": "tool",
                    "command": ["python", "analysis.py"],
                    "usage": {"input_tokens": 12, "output_tokens": 8, "total_tokens": 20},
                }
            ),
        ]
    )
    result = summarize_jsonl(events)
    assert result["event_summary"] == {"started": 1, "tool": 1}
    assert result["observable_commands"] == ["python argc=2"]
    assert result["token_usage"]["total_tokens"] == 20


def test_missing_token_usage_is_compatible():
    assert summarize_jsonl(json.dumps({"type": "message"}))["token_usage"] is None


def test_invalid_jsonl_is_counted_not_hidden():
    result = summarize_jsonl("not-json\n")
    assert result["event_summary"]["invalid_jsonl_line"] == 1


def test_error_sanitization_redacts_secret_assignments_and_home_paths(tmp_path):
    fake_key = "s" + "k-" + "abcdefghijklmnopqrstuvwxyz123456"
    fake_private_path = "/" + "home/person/private"
    text = f"token=secret-value {fake_key} at {fake_private_path} and " + str(tmp_path)
    cleaned = sanitize_error(text, tmp_path)
    assert "secret-value" not in cleaned
    assert fake_key not in cleaned
    assert fake_private_path not in cleaned
    assert "<REPO_ROOT>" in cleaned
