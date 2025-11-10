"""Utility functions for evaluations"""

import subprocess
import json
import tempfile
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import yaml
import urllib.request
import urllib.error
import time
import threading


# Load judge system prompt at module initialization
_judge_prompt_path = Path(__file__).parent.parent / 'config' / 'judge_system_prompt.yaml'
with open(_judge_prompt_path, 'r') as f:
    _judge_prompts = yaml.safe_load(f)
    JUDGE_PROMPT_TEMPLATE = _judge_prompts['judge_prompt']['instruction_template']


# Global rate limiter to prevent hitting Claude CLI limits
class RateLimiter:
    """Simple rate limiter with configurable delay between requests."""
    
    def __init__(self, min_interval: float = 2.0):
        """
        Initialize rate limiter.
        
        Args:
            min_interval: Minimum seconds between requests (default: 2.0)
        """
        self.min_interval = min_interval
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def wait(self):
        """Wait until enough time has passed since last request."""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()


# Global rate limiter instance
_rate_limiter = RateLimiter(min_interval=2.0)


def load_source(source_type: str, location: str, s3_client=None, bucket_name: str = None, base_path: str = None) -> dict:
    """Load evaluation YAML from various sources (url, s3_key, inline, or file)"""
    if source_type == "file":
        if base_path:
            file_path = Path(base_path) / location
        else:
            file_path = Path(location)
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    
    elif source_type == "url":
        with urllib.request.urlopen(location) as response:
            return yaml.safe_load(response.read().decode('utf-8'))
    
    elif source_type == "s3_key":
        if not s3_client or not bucket_name:
            raise ValueError("S3 client and bucket_name required for s3_key source")
        response = s3_client.get_object(Bucket=bucket_name, Key=location)
        return yaml.safe_load(response['Body'].read().decode('utf-8'))
    
    elif source_type == "inline":
        return yaml.safe_load(location)
    
    raise ValueError(f"Unknown source type: {source_type}")


def clone_repo(repo_url: str) -> Path:
    """Clone GitHub repository to temp directory"""
    temp_dir = Path(tempfile.mkdtemp(prefix="eval-"))
    
    result = subprocess.run(
        ['git', 'clone', '--depth', '1', repo_url, str(temp_dir)],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode != 0:
        raise Exception(f"Failed to clone repository: {result.stderr}")
    
    return temp_dir


def build_prompt(eval_dict: dict) -> str:
    """Build prompt for evaluator agent with variable substitution support"""
    
    # Get criteria
    criteria = eval_dict['criteria']
    inputs = eval_dict.get('inputs', {})
    
    # Perform variable substitution for {variable_name} syntax in criteria
    if inputs:
        for key, value in inputs.items():
            if value is not None:
                # Replace {key} with value in criteria
                placeholder = f"{{{key}}}"
                criteria = criteria.replace(placeholder, str(value))
    
    # Build inputs section for reference
    inputs_section = ""
    if inputs:
        inputs_section = "\n\nProvided Inputs:\n"
        for key, value in inputs.items():
            if value is not None:
                inputs_section += f"- {key}: {value}\n"
    
    # Use the judge prompt template from YAML
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        criteria=criteria,
        inputs_section=inputs_section
    )
    
    return prompt


def run_eval(temp_dir: Path, prompt: str, timeout: int = 300, max_retries: int = 3) -> bool:
    """
    Run Claude CLI evaluator to analyze the work with rate limiting and retries.
    
    Args:
        temp_dir: Directory to run evaluation in
        prompt: Evaluation prompt
        timeout: Timeout in seconds
        max_retries: Maximum retry attempts for rate limits (default: 3)
    
    Returns:
        True if evaluation completed, False if timeout
    """
    for attempt in range(max_retries):
        try:
            # Wait for rate limiter (adds 2s delay between requests)
            _rate_limiter.wait()
            
            result = subprocess.run(
                ['claude', '-p', prompt, '--dangerously-skip-permissions'],
                cwd=str(temp_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            # Check for rate limits
            is_rate_limited = (
                (result.stdout and "Session limit reached" in result.stdout) or
                (result.stderr and "Session limit reached" in result.stderr)
            )
            
            if is_rate_limited:
                if attempt < max_retries - 1:
                    # Exponential backoff: 10s, 30s, 90s
                    wait_time = 10 * (3 ** attempt)
                    print(f"⚠️  Rate limit hit, waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise RuntimeError(f"Claude CLI rate limit reached after {max_retries} attempts. Please wait and try again later.")
            
            # Success - no rate limit
            return True
            
        except subprocess.TimeoutExpired:
            return False
        except FileNotFoundError:
            raise RuntimeError("Claude CLI not found - ensure it's installed")
    
    return False


def run_batch_eval(
    temp_dir: Path,
    eval_specs: list,
    timeout: int = None,
    max_retries: int = 3
) -> dict:
    """
    Run multiple evaluations in a single Claude session.
    
    Args:
        temp_dir: Repository directory to evaluate
        eval_specs: List of eval specifications (loaded YAML dicts)
        timeout: Total timeout (default: 300s per eval)
        max_retries: Max retry attempts for rate limits
    
    Returns:
        Dict mapping eval_id -> result dict (or error dict if failed)
    
    Example:
        eval_specs = [
            load_source("file", "evals/nextjs/001.yaml"),
            load_source("file", "evals/react/001.yaml"),
        ]
        results = run_batch_eval(temp_dir, eval_specs)
        # Returns: {
        #   "nextjs_server_component_fetch_001": {...result...},
        #   "react_missing_useeffect_dependencies_001": {...result...}
        # }
    """
    if not eval_specs:
        return {}
    
    # Calculate timeout: 300s per eval if not specified
    if timeout is None:
        timeout = len(eval_specs) * 300
    
    # Build batch criteria section
    batch_criteria = []
    for i, spec in enumerate(eval_specs, 1):
        eval_id = spec['eval_id']
        criteria = spec['criteria']
        
        # Perform input substitution
        inputs = spec.get('inputs', {})
        if inputs:
            for key, value in inputs.items():
                if value is not None:
                    criteria = criteria.replace(f"{{{key}}}", str(value))
        
        batch_criteria.append(f"""
{'='*80}
EVALUATION {i}/{len(eval_specs)}
{'='*80}
EVAL ID: {eval_id}
FILENAME: eval_result_{eval_id}.json

CRITERIA:
{criteria}
""")
    
    # Load batch prompt template
    judge_prompt_path = Path(__file__).parent.parent / 'config' / 'judge_system_prompt.yaml'
    with open(judge_prompt_path, 'r') as f:
        prompts = yaml.safe_load(f)
        template = prompts['batch_judge_prompt']['instruction_template']
    
    # Build final prompt
    prompt = template.format(
        eval_count=len(eval_specs),
        batch_criteria='\n'.join(batch_criteria)
    )
    
    # Run Claude (with rate limiting and retries)
    for attempt in range(max_retries):
        try:
            _rate_limiter.wait()
            
            result = subprocess.run(
                ['claude', '-p', prompt, '--dangerously-skip-permissions'],
                cwd=str(temp_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            # Check for rate limits
            is_rate_limited = (
                (result.stdout and "Session limit reached" in result.stdout) or
                (result.stderr and "Session limit reached" in result.stderr)
            )
            
            if is_rate_limited and attempt < max_retries - 1:
                wait_time = 10 * (3 ** attempt)
                print(f"⚠️  Rate limit hit, waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                time.sleep(wait_time)
                continue
            elif is_rate_limited:
                raise RuntimeError(f"Claude CLI rate limit reached after {max_retries} attempts")
            
            break
            
        except subprocess.TimeoutExpired:
            # Timeout - but some evals may have completed, collect what we can
            print(f"⚠️  Batch evaluation timed out after {timeout}s. Collecting partial results...")
            break
        except FileNotFoundError:
            raise RuntimeError("Claude CLI not found - ensure it's installed")
    
    # Collect results for each eval
    results = {}
    for spec in eval_specs:
        eval_id = spec['eval_id']
        result_file = temp_dir / f"eval_result_{eval_id}.json"
        
        if result_file.exists():
            try:
                with open(result_file, 'r') as f:
                    content = f.read()
                    start = content.find('{')
                    end = content.rfind('}')
                    if start != -1 and end != -1:
                        json_str = content[start:end+1]
                        results[eval_id] = json.loads(json_str)
                    else:
                        results[eval_id] = {
                            "status": "error",
                            "score": 0.0,
                            "error": "Invalid JSON format in result file"
                        }
            except Exception as e:
                results[eval_id] = {
                    "status": "error",
                    "score": 0.0,
                    "error": f"Failed to parse result: {str(e)}"
                }
        else:
            results[eval_id] = {
                "status": "error",
                "score": 0.0,
                "error": "Result file not created"
            }
    
    return results


def read_result(temp_dir: Path) -> dict:
    """Read evaluation result JSON from temp directory"""
    result_file = temp_dir / 'eval_result.json'
    if not result_file.exists():
        raise FileNotFoundError("No eval_result.json found")
    
    with open(result_file, 'r') as f:
        content = f.read()
        
        # Try to find JSON object in the content (handle extra text before/after)
        # Look for the first { and last }
        start = content.find('{')
        end = content.rfind('}')
        
        if start == -1 or end == -1 or start >= end:
            raise ValueError(f"No valid JSON object found in eval_result.json. Content: {content[:200]}")
        
        json_str = content[start:end+1]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}. Content: {json_str[:200]}")


def save_results(result: dict, eval_spec: dict, repo_url: str, output_dir: str = "results") -> Path:
    """Save results to file"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{eval_spec['eval_id']}_{timestamp}.json"
    output_file = output_path / filename
    
    result['metadata'] = {
        'eval_id': eval_spec['eval_id'],
        'eval_name': eval_spec['name'],
        'repo_url': repo_url,
        'timestamp': datetime.now().isoformat(),
        'evaluator': 'claude'
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    return output_file

