"""
Token estimation module for File Tree Generator.

This module provides functionality to estimate token counts for different language models.
It uses simple approximation methods that can be adjusted with model-specific factors.
"""

import re
import os
import json
from typing import Dict, Tuple, List, Any, Optional

# Define known models with their approximate token factors
# These are estimations and can be adjusted as needed
MODEL_FACTORS = {
    "claude-3.5-sonnet": {
        "char_factor": 0.25,         # Characters per token (approximate)
        "word_factor": 1.3,          # Tokens per word (approximate)
        "name": "Claude 3.5 Sonnet"
    },
    "claude-3-opus": {
        "char_factor": 0.25,         # Characters per token (approximate)
        "word_factor": 1.3,          # Tokens per word (approximate)
        "name": "Claude 3 Opus"
    },
    "claude-3-haiku": {
        "char_factor": 0.25,         # Characters per token (approximate)
        "word_factor": 1.3,          # Tokens per word (approximate)
        "name": "Claude 3 Haiku"
    },
    "gpt-4": {
        "char_factor": 0.25,         # Characters per token (approximate)
        "word_factor": 1.3,          # Tokens per word (approximate)
        "name": "GPT-4"
    },
    "gpt-3.5-turbo": {
        "char_factor": 0.25,         # Characters per token (approximate)
        "word_factor": 1.3,          # Tokens per word (approximate)
        "name": "GPT-3.5 Turbo"
    },
    "custom": {
        "char_factor": 0.25,         # Default, user configurable
        "word_factor": 1.3,          # Default, user configurable
        "name": "Custom Model"
    }
}

def get_available_models():
    """Get a list of available model names for display in UI"""
    return [(model_id, factor['name']) for model_id, factor in MODEL_FACTORS.items()]

def estimate_tokens_for_text(text, model="claude-3.5-sonnet", method="char"):
    """
    Estimate token count for a given text.
    
    Args:
        text: The text to estimate tokens for
        model: Model ID from MODEL_FACTORS
        method: Estimation method ('char' or 'word')
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
        
    # Get model factors, defaulting to Claude 3.5 Sonnet if not found
    factors = MODEL_FACTORS.get(model, MODEL_FACTORS["claude-3.5-sonnet"])
    
    if method == "char":
        # Character-based estimation
        return int(len(text) * factors["char_factor"])
    elif method == "word":
        # Word-based estimation
        word_count = len(re.findall(r'\S+', text))
        return int(word_count * factors["word_factor"])
    else:
        # Default to character-based estimation
        return int(len(text) * factors["char_factor"])

def estimate_tokens_for_file(file_path, model="claude-3.5-sonnet", method="char"):
    """
    Estimate token count for a file.
    
    Args:
        file_path: Path to the file
        model: Model ID from MODEL_FACTORS
        method: Estimation method ('char' or 'word')
        
    Returns:
        (success, token_count, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return True, estimate_tokens_for_text(content, model, method), None
    except Exception as e:
        return False, 0, str(e)

def estimate_tokens_for_directory(directory, extensions=None, blacklist_folders=None, 
                               blacklist_files=None, model="claude-3.5-sonnet", 
                               method="char", max_files=None):
    """
    Estimate token count for all matching files in a directory.
    
    Args:
        directory: Root directory to scan
        extensions: File extensions to include (None for all)
        blacklist_folders: Folders to exclude
        blacklist_files: Files to exclude
        model: Model ID from MODEL_FACTORS
        method: Estimation method ('char' or 'word')
        max_files: Maximum number of files to process (None for all)
        
    Returns:
        Dictionary with token estimation results
    """
    blacklist_folders = set(blacklist_folders or [])
    blacklist_files = set(blacklist_files or [])
    
    # Convert extensions to a set for faster lookup
    if extensions:
        extensions = set(extensions)
    
    total_tokens = 0
    processed_files = 0
    skipped_files = 0
    tokens_by_extension = {}
    largest_files = []  # Will hold (file_path, token_count) tuples
    
    # Walk through directory
    for root, dirs, files in os.walk(directory):
        # Skip blacklisted folders
        dirs[:] = [d for d in dirs if d not in blacklist_folders]
        
        for file in files:
            # Skip blacklisted files
            if file in blacklist_files:
                continue
                
            # Check extensions if provided
            if extensions:
                _, ext = os.path.splitext(file)
                if ext.lower() not in extensions:
                    continue
            
            # Check if we've reached the maximum number of files
            if max_files is not None and processed_files >= max_files:
                skipped_files += 1
                continue
                
            file_path = os.path.join(root, file)
            
            # Estimate tokens for this file
            success, token_count, _ = estimate_tokens_for_file(file_path, model, method)
            if success:
                total_tokens += token_count
                processed_files += 1
                
                # Track tokens by extension
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                if ext not in tokens_by_extension:
                    tokens_by_extension[ext] = {"files": 0, "tokens": 0}
                tokens_by_extension[ext]["files"] += 1
                tokens_by_extension[ext]["tokens"] += token_count
                
                # Update largest files list
                largest_files.append((file_path, token_count))
                largest_files.sort(key=lambda x: x[1], reverse=True)
                largest_files = largest_files[:10]  # Keep only top 10
            else:
                skipped_files += 1
    
    # Create result summary
    result = {
        "total_tokens": total_tokens,
        "processed_files": processed_files,
        "skipped_files": skipped_files,
        "tokens_by_extension": tokens_by_extension,
        "largest_files": largest_files,
        "model": model,
        "model_name": MODEL_FACTORS[model]["name"],
        "method": method
    }
    
    return result

def format_token_summary(token_result, root_dir=None):
    """
    Format token estimation summary as a string.
    
    Args:
        token_result: Result dictionary from estimate_tokens_for_directory
        root_dir: Root directory for creating relative paths
        
    Returns:
        Multi-line string with token summary
    """
    lines = []
    lines.append("TOKEN ESTIMATION SUMMARY")
    lines.append("=" * 80)
    lines.append(f"Model: {token_result['model_name']}")
    lines.append(f"Method: {'Character-based' if token_result['method'] == 'char' else 'Word-based'}")
    lines.append(f"Total estimated tokens: {token_result['total_tokens']:,}")
    lines.append(f"Files processed: {token_result['processed_files']}")
    if token_result['skipped_files'] > 0:
        lines.append(f"Files skipped: {token_result['skipped_files']}")
    
    # Add extension breakdown
    if token_result['tokens_by_extension']:
        lines.append("\nTokens by file extension:")
        for ext, data in sorted(token_result['tokens_by_extension'].items(), 
                              key=lambda x: x[1]['tokens'], reverse=True):
            lines.append(f"  {ext}: {data['tokens']:,} tokens in {data['files']} files " + 
                       f"(avg: {data['tokens'] / max(1, data['files']):,.0f} per file)")
    
    # Add largest files
    if token_result['largest_files']:
        lines.append("\nLargest files by token count:")
        for file_path, token_count in token_result['largest_files']:
            if root_dir:
                rel_path = os.path.relpath(file_path, root_dir)
                lines.append(f"  {rel_path}: {token_count:,} tokens")
            else:
                lines.append(f"  {file_path}: {token_count:,} tokens")
    
    return "\n".join(lines)

def compare_token_estimates(raw_result, processed_result):
    """
    Compare raw and processed token estimates.
    
    Args:
        raw_result: Token estimation result for raw files
        processed_result: Token estimation result for processed output
        
    Returns:
        Multi-line string with comparison summary
    """
    lines = []
    lines.append("TOKEN COMPARISON SUMMARY")
    lines.append("=" * 80)
    
    raw_tokens = raw_result['total_tokens']
    processed_tokens = processed_result['total_tokens']
    
    lines.append(f"Raw files: {raw_tokens:,} tokens in {raw_result['processed_files']} files")
    lines.append(f"Processed output: {processed_tokens:,} tokens")
    
    if raw_tokens > 0:
        ratio = processed_tokens / raw_tokens
        change = processed_tokens - raw_tokens
        change_percent = (change / raw_tokens) * 100
        
        lines.append(f"Token change: {change:+,} tokens ({change_percent:+.1f}%)")
        lines.append(f"Processed/Raw ratio: {ratio:.2f}")
        
        if processed_tokens < raw_tokens:
            lines.append("✅ Processing reduced token count")
        else:
            lines.append("⚠️ Processing increased token count")
    
    return "\n".join(lines)

def save_custom_model_factors(char_factor, word_factor):
    """
    Save custom model factors to the global definition.
    
    Args:
        char_factor: Character factor for custom model
        word_factor: Word factor for custom model
        
    Returns:
        None
    """
    MODEL_FACTORS["custom"]["char_factor"] = char_factor
    MODEL_FACTORS["custom"]["word_factor"] = word_factor

def get_model_factors(model_id):
    """
    Get factors for a specific model.
    
    Args:
        model_id: ID of the model
        
    Returns:
        Dictionary with model factors
    """
    return MODEL_FACTORS.get(model_id, MODEL_FACTORS["claude-3.5-sonnet"])