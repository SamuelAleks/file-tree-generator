"""
Unit tests for the token_estimator module.
"""

import os
import pytest
from pathlib import Path
import token_estimator


def test_estimate_tokens_for_text():
    """Test token estimation for text based on different models and methods."""
    text = "This is a sample text for testing token estimation."
    
    # Test character-based estimation
    char_estimate = token_estimator.estimate_tokens_for_text(text, "claude-3.5-sonnet", "char")
    assert char_estimate > 0, "Character-based estimation should return positive token count"
    
    # Test word-based estimation
    word_estimate = token_estimator.estimate_tokens_for_text(text, "claude-3.5-sonnet", "word")
    assert word_estimate > 0, "Word-based estimation should return positive token count"
    
    # Test different models
    models = ["claude-3-opus", "gpt-4", "claude-3.7-sonnet"]
    for model in models:
        estimate = token_estimator.estimate_tokens_for_text(text, model, "char")
        assert estimate > 0, f"{model} estimation should return positive token count"


def test_estimate_tokens_for_empty_text():
    """Test token estimation for empty text."""
    empty_text = ""
    estimate = token_estimator.estimate_tokens_for_text(empty_text)
    assert estimate == 0, "Empty text should have 0 tokens"


def test_estimate_tokens_for_file(sample_project):
    """Test token estimation for a file."""
    file_path = os.path.join(sample_project, "src", "main.py")
    
    # Verify the file exists
    assert os.path.exists(file_path), f"Test file not found: {file_path}"
    
    # Test estimation
    success, token_count, error = token_estimator.estimate_tokens_for_file(file_path)
    
    assert success is True, f"File estimation should succeed, got error: {error}"
    assert token_count > 0, "File estimation should return positive token count"
    assert error is None, f"Error should be None, got: {error}"


def test_estimate_tokens_for_nonexistent_file():
    """Test token estimation for a nonexistent file."""
    file_path = "nonexistent_file.txt"
    success, token_count, error = token_estimator.estimate_tokens_for_file(file_path)
    
    assert success is False, "Estimation should fail for nonexistent file"
    assert token_count == 0, "Token count should be 0 for failed estimation"
    assert error is not None, "Error message should be provided"


def test_estimate_tokens_for_directory(sample_project):
    """Test token estimation for a directory."""
    # Test with Python files only
    result = token_estimator.estimate_tokens_for_directory(
        sample_project,
        extensions=[".py"],
        blacklist_folders=[],
        blacklist_files=[]
    )
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert result["total_tokens"] > 0, "Total tokens should be positive"
    assert result["processed_files"] == 2, f"Should process 2 Python files, got {result['processed_files']}"
    assert ".py" in result["tokens_by_extension"], "Extensions should include .py"
    
    # Test with all supported extensions
    result_all = token_estimator.estimate_tokens_for_directory(
        sample_project,
        extensions=[".py", ".md"],
        blacklist_folders=[],
        blacklist_files=[]
    )
    
    assert result_all["processed_files"] == 3, f"Should process 3 files, got {result_all['processed_files']}"
    assert result_all["total_tokens"] > result["total_tokens"], "All extensions should yield more tokens"


def test_format_token_summary():
    """Test the summary formatting function."""
    mock_result = {
        "total_tokens": 1000,
        "processed_files": 5,
        "skipped_files": 2,
        "tokens_by_extension": {
            ".py": {"files": 3, "tokens": 600},
            ".md": {"files": 2, "tokens": 400}
        },
        "largest_files": [
            ("/path/to/file1.py", 300),
            ("/path/to/file2.py", 200)
        ],
        "model": "claude-3.5-sonnet",
        "model_name": "Claude 3.5 Sonnet",
        "method": "char"
    }
    
    summary = token_estimator.format_token_summary(mock_result, "/path/to")
    
    assert "TOKEN ESTIMATION SUMMARY" in summary, "Summary should have a title"
    assert "Claude 3.5 Sonnet" in summary, "Summary should include model name"
    assert "1,000" in summary, "Summary should include formatted token count"
    assert ".py" in summary, "Summary should include extension breakdown"
    assert "file1.py" in summary, "Summary should include largest files"


def test_custom_model_factors():
    """Test setting and using custom model factors."""
    text = "This is a test text"
    
    # Get default estimate
    default_estimate = token_estimator.estimate_tokens_for_text(text, "custom", "char")
    
    # Set custom factors
    token_estimator.save_custom_model_factors(0.5, 2.0)
    
    # Get new estimate
    new_estimate = token_estimator.estimate_tokens_for_text(text, "custom", "char")
    
    # The new estimate should be different from the default
    assert new_estimate != default_estimate, "Custom factors should change the estimate"
    
    # Reset to default
    token_estimator.save_custom_model_factors(0.25, 1.3)