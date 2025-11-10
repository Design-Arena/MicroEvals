# MicroEvals: Complete Agent Documentation

**Version:** 0.1.0  
**Last Updated:** November 10, 2025  
**License:** MIT

> **Purpose:** This document provides AI agents with everything they need to understand, use, and contribute to the MicroEvals framework.

---

## Table of Contents

1. [What is MicroEvals?](#1-what-is-microevals)
2. [Core Concepts](#2-core-concepts)
3. [Repository Structure](#3-repository-structure)
4. [Running Evaluations](#4-running-evaluations)
5. [Creating New Evaluations](#5-creating-new-evaluations)
6. [Understanding Results](#6-understanding-results)
7. [Technical Architecture](#7-technical-architecture)
8. [Contributing Guidelines](#8-contributing-guidelines)
9. [Best Practices for Agents](#9-best-practices-for-agents)
10. [Common Workflows](#10-common-workflows)
11. [Troubleshooting](#11-troubleshooting)
12. [API Reference](#12-api-reference)

---

## 1. What is MicroEvals?

### Overview

MicroEvals is an **automated evaluation framework** for AI-generated code quality and best practices. It uses Claude (via the Claude CLI) as an intelligent judge to analyze codebases against specific criteria.

**Key Distinction:** Unlike traditional linters that check syntax, MicroEvals uses LLM-as-judge to understand **context** and evaluate **architectural decisions**.

### Purpose

- **Validate AI-generated code** against framework-specific best practices
- **Catch anti-patterns** that traditional linters miss
- **Ensure quality** across different technology stacks
- **Provide objective scoring** for code quality metrics

### Technology Stack

```yaml
Language: Python 3.8+
Dependencies:
  - requests >= 2.31.0
  - pyyaml >= 6.0
  - python-dotenv >= 1.0.0
External Tools:
  - Claude CLI (required)
  - Git (required)
```

### Supported Frameworks

| Category | Count | Technologies |
|----------|-------|--------------|
| **nextjs** | 20+ | Next.js App Router, server/client components, routing |
| **react** | 7+ | React hooks, state management, Zustand |
| **supabase** | 17+ | Auth, database, storage, RLS security |
| **tailwind** | 4+ | Tailwind CSS configuration and usage |
| **typescript** | 2+ | Type safety, null checks |
| **vercel** | 3+ | Deployment, environment variables, SEO |
| **shadcn** | 7+ | shadcn/ui component library integration |

---

## 2. Core Concepts

### What is a MicroEval?

A **MicroEval** is a focused, single-purpose test that checks for one specific pattern or anti-pattern. Each eval is:

- **Atomic**: Tests one thing only
- **Declarative**: Written in YAML with clear criteria
- **Context-aware**: Uses Claude to understand code semantically
- **Scored**: Returns 1.0 (pass), 0.0 (fail), or -1.0 (N/A)

### The Scoring System

```python
# Scoring logic
1.0  = PASS     # All criteria met, no anti-patterns found
0.0  = FAIL     # Anti-pattern detected OR criteria not met
-1.0 = N/A      # Pattern/feature not present in codebase
```

**Important distinctions:**

- **0.0 vs -1.0**: If code *attempts* the pattern but does it wrong → 0.0. If pattern doesn't exist at all → -1.0
- **Example**: Evaluating Next.js server components in a React-only app → -1.0 (N/A)
- **Example**: Server component exists but uses incorrect async pattern → 0.0 (FAIL)

### Eval Lifecycle

```
1. Load eval YAML file
   ↓
2. Clone target repository
   ↓
3. Build evaluation prompt (with input substitution)
   ↓
4. Run Claude CLI with codebase access
   ↓
5. Claude analyzes code, creates eval_result.json
   ↓
6. Parse result, save to results/ directory
   ↓
7. Display colored terminal output
   ↓
8. Cleanup temporary files
```

### Batch Mode vs Single Mode

**Single Mode:**
- Runs one eval per Claude session
- More resilient (failures isolated)
- Slower (multiple Claude invocations)
- 2-second delay between evals (rate limiting)

**Batch Mode:**
- Runs multiple evals in one Claude session
- Faster (single context window)
- More efficient Claude usage
- Better for related evaluations
- Specify with `--batch-size N`

---

## 3. Repository Structure

### Directory Layout

```
MicroEvals/
│
├── microevals/                 # Main Python package
│   ├── __init__.py             # Package exports
│   ├── eval_runner.py          # CLI for running evals (484 lines)
│   ├── eval_registry.py        # Eval discovery and metadata (209 lines)
│   └── utils.py                # Core utilities (377 lines)
│
├── evals/                      # Evaluation definitions (YAML files)
│   ├── nextjs/                 # Next.js-specific evals
│   │   ├── 001-server-component.yaml
│   │   ├── 002-client-component.yaml
│   │   ├── 003-cookies.yaml
│   │   └── ... (20+ files)
│   │
│   ├── react/                  # React-specific evals
│   │   ├── 001_missing_useeffect_dependencies.yaml
│   │   └── ... (7+ files)
│   │
│   ├── supabase/               # Supabase-specific evals
│   │   ├── 001_client_setup.yaml
│   │   ├── 002_auth_context_setup.yaml
│   │   └── ... (17+ files)
│   │
│   ├── tailwind/               # Tailwind CSS evals (4 files)
│   ├── typescript/             # TypeScript evals (2 files)
│   ├── vercel/                 # Vercel deployment evals (3 files)
│   └── shadcn/                 # shadcn/ui evals (7+ files)
│
├── config/                     # Configuration files
│   ├── judge_system_prompt.yaml    # Claude judge prompt templates
│   └── example_repos.json          # Test repositories
│
├── results/                    # Evaluation results (auto-generated, gitignored)
│   └── *.json                  # Result files with timestamps
│
├── requirements.txt            # Python dependencies
├── CONTRIBUTING.md             # Contribution guidelines (267 lines)
├── README.md                   # User documentation (469 lines)
├── LICENSE                     # MIT License
└── .gitignore                  # Ignores results/, venv/, etc.
```

### Key Files Explained

#### `microevals/eval_runner.py`
- **Purpose**: Main CLI entry point
- **Functionality**: Orchestrates eval execution, handles parallelism, batch mode
- **Key Functions**: `run_single_eval()`, `print_result_line()`, `print_summary()`, `main()`

#### `microevals/eval_registry.py`
- **Purpose**: Discovers and catalogs all evals
- **Functionality**: Provides search, filtering, metadata extraction
- **Key Class**: `EvalRegistry` with methods like `get_by_category()`, `get_by_id()`, `filter_by_requirements()`

#### `microevals/utils.py`
- **Purpose**: Core utility functions
- **Functionality**: Repo cloning, prompt building, Claude execution, result parsing
- **Key Functions**: `clone_repo()`, `build_prompt()`, `run_eval()`, `run_batch_eval()`, `read_result()`, `save_results()`
- **Rate Limiting**: Implements 2-second delay between Claude requests

#### `config/judge_system_prompt.yaml`
- **Purpose**: System prompts for Claude judge
- **Templates**: 
  - `judge_prompt`: Single eval template
  - `batch_judge_prompt`: Batch eval template
- **Critical**: Instructs Claude to score objectively and create JSON output

### Naming Conventions

#### Eval IDs
```
Format: category_descriptive_name_nnn

Examples:
- nextjs_server_component_001
- react_missing_useeffect_dependencies_001
- supabase_client_setup
```

#### File Names
```
Format: nnn-descriptive-name.yaml  OR  nnn_descriptive_name.yaml

Examples:
- 001-server-component.yaml
- 001_missing_useeffect_dependencies.yaml
- 011-security-rls-policies.yaml
```

**Note**: Both hyphen and underscore styles are acceptable.

---

## 4. Running Evaluations

### Installation

```bash
# Install from PyPI
pip install microevals

# Verify installation
microeval --help
```

### Prerequisites

```bash
# 1. Python 3.8+ installed
python --version  # Should be 3.8 or higher

# 2. Claude CLI installed and authenticated
claude --version  # Should return version number

# 3. Git installed (for remote repositories)
git --version
```

### Safety Guarantees

When running on local directories, MicroEvals provides bulletproof safety:

- **Your code is COPIED to a temporary directory** (never modified in place)
- **6 independent safety checks** before any directory deletion:
  1. Path must be inside system temp directory
  2. Directory name must start with `eval-`
  3. Must contain MicroEvals safety marker file
  4. Must not be current working directory
  5. Must not be home directory
  6. Must not contain home directory
- **If ANY check fails**, deletion is refused with a warning message
- **Original files are never touched** - they remain exactly as they were

### Basic Usage

#### Run on Current Directory (Recommended)

```bash
# Navigate to your project
cd your-nextjs-app

# Run a single eval
microeval --eval evals/nextjs/001-server-component.yaml

# Run all evals in a category
microeval --category nextjs

# Run all evals
microeval --all
```

#### Run on Remote Repository

```bash
# Run a single eval
microeval --repo https://github.com/user/app \
  --eval evals/nextjs/001-server-component.yaml

# Run all evals in a category
microeval --repo https://github.com/user/app --category nextjs

# Run all evals
microeval --repo https://github.com/user/app --all
```

#### Run Specific Eval IDs

```bash
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --ids nextjs_server_component_001 react_missing_useeffect_dependencies_001
```

#### Run Multiple Specific Files

```bash
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --evals evals/nextjs/001-server-component.yaml evals/react/001_missing_useeffect_dependencies.yaml
```

### Advanced Usage

#### Runtime Input Overrides

Override default values from eval YAML files:

```bash
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --eval evals/supabase/001_client_setup.yaml \
  --input supabase_url "https://xyz.supabase.co" \
  --input supabase_anon_key "your_key_here"
```

**Use case**: When eval requires runtime-specific values (URLs, API keys, deployment URLs)

#### Parallel Execution

Run multiple evals simultaneously:

```bash
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --category nextjs \
  --parallel 3
```

**Benefits**: Faster execution
**Drawback**: Uses more system resources, multiple Claude sessions

#### Batch Mode (Recommended for Speed)

Run multiple evals in a single Claude session:

```bash
# Small batches
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --category tailwind \
  --batch-size 5

# Large batches (most efficient)
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --all \
  --batch-size 15
```

**Benefits**:
- Much faster (single Claude context)
- More efficient token usage
- Better for related evaluations

**Drawback**:
- If batch fails, all evals in batch may fail
- Less granular error handling

#### Preview Batch Prompt

Before running, inspect what will be sent to Claude:

```bash
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --category tailwind \
  --batch-size 3 \
  --print-prompt
```

This pauses for confirmation before execution.

#### Custom Timeout

For large codebases or complex evals:

```bash
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --eval evals/nextjs/030_app_router_migration.yaml \
  --timeout 600  # 10 minutes
```

Default: 300 seconds (5 minutes)

#### Custom Output Directory

```bash
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --category nextjs \
  --output-dir my_custom_results
```

Default: `results/` (gitignored)

### Listing Available Evals

```bash
# List all evals
python -m microevals.eval_registry --list

# Filter by category
python -m microevals.eval_registry --category nextjs
```

---

## 5. Creating New Evaluations

### Eval YAML Structure

Every eval is a YAML file with this structure:

```yaml
# REQUIRED FIELDS

eval_id: category_descriptive_name_001
  # Unique identifier
  # Format: category_name_nnn
  # Used for result filenames and references

name: "Human-Readable Name"
  # Display name shown in terminal output
  # Should be concise but descriptive

description: "Brief description of what this eval checks"
  # One-sentence summary
  # Helps users understand purpose

category: nextjs
  # Category slug: nextjs, react, supabase, tailwind, typescript, vercel, shadcn
  # Determines organization in evals/ directory

criteria: |
  # The actual evaluation criteria (multi-line string)
  # This becomes part of the prompt sent to Claude
  # See detailed structure below

# OPTIONAL FIELDS

inputs:
  # Runtime-configurable variables
  # Can be overridden with --input flag
  custom_variable: "default_value"
  deployment_url: null  # null = required at runtime
```

### Criteria Format

The `criteria` field is the heart of every eval. Use this template:

```yaml
criteria: |
  You have access to the entire codebase. Evaluate [specific pattern/issue].
  
  CONTEXT: This eval applies to [when it's relevant, e.g., "Next.js App Router apps with authentication"].
  
  WHAT TO LOOK FOR:
  Look for [specific files, patterns, or code structures].
  [Be concrete: mention file patterns, function names, import statements, etc.]
  
  ANTI-PATTERN (mark as failed):
  - [Specific bad pattern 1 with code example if possible]
  - [Specific bad pattern 2]
  - [Common mistake to catch]
  
  WHY IT'S WRONG (optional but recommended):
  - [Explanation of why this matters]
  - [Consequences of the anti-pattern]
  
  CORRECT PATTERN (mark as passed):
  - [Ideal implementation 1]
  - [Alternative correct approach 2]
  - [Best practice to follow]
  
  MARK AS N/A if:
  - [Condition that makes eval not applicable]
  - [Another condition for N/A]
  - [When feature doesn't exist in codebase]
  
  SCORING:
  - Score 1.0 (PASS): [Specific conditions for passing]
  - Score 0.0 (FAIL): [Specific conditions for failing]
  - Score -1.0 (N/A): [Specific conditions for N/A]
```

### Variable Substitution

Use `{variable_name}` syntax in criteria for runtime inputs:

```yaml
inputs:
  deployment_url: "https://example.com"
  min_components: "3"

criteria: |
  Check the deployment at {deployment_url}.
  Verify at least {min_components} components are present.
```

At runtime, these get replaced:
```bash
python -m microevals.eval_runner \
  --eval my-eval.yaml \
  --repo URL \
  --input deployment_url "https://myapp.vercel.app" \
  --input min_components "5"
```

### Complete Example: React useEffect Eval

```yaml
eval_id: react_missing_useeffect_dependencies_001
name: "Missing Dependencies in useEffect"
description: "Checks if useEffect hooks include all dependencies in their dependency array"
category: react

criteria: |
  Detect useEffect with missing dependencies causing stale closures.
  
  ANTI-PATTERN:
  - useEffect(() => { doSomething(prop) }, []) // prop not in deps
  - useEffect(() => { fetch(url) }, []) // url not in deps
  - Using props/state inside effect without listing them
  
  WHY IT'S WRONG:
  - Stale closures - effect uses old values
  - Effect doesn't re-run when dependencies change
  - Subtle bugs that are hard to debug
  - React ESLint rule: exhaustive-deps
  
  CORRECT:
  - useEffect(() => { doSomething(prop) }, [prop])
  - Include ALL variables from outer scope used in effect
  - Or use useCallback/useMemo to stabilize references
  
  SCORING:
  - Score 1.0 (PASS): useEffect hooks exist AND all include correct dependencies
  - Score 0.0 (FAIL): useEffect hooks exist BUT missing dependencies found
  - Score -1.0 (N/A): No useEffect hooks found in codebase
```

### Testing Your Eval

#### 1. Test Against Known Repositories

You need at least 3 test cases:

```bash
# Should PASS
python -m microevals.eval_runner \
  --repo https://github.com/user/good-example \
  --eval evals/your-category/your-eval.yaml

# Should FAIL
python -m microevals.eval_runner \
  --repo https://github.com/user/bad-example \
  --eval evals/your-category/your-eval.yaml

# Should be N/A
python -m microevals.eval_runner \
  --repo https://github.com/user/unrelated-app \
  --eval evals/your-category/your-eval.yaml
```

#### 2. Check Result Files

```bash
cat results/your_eval_id_*.json
```

Verify:
- Score is correct (1.0, 0.0, or -1.0)
- Summary is clear and accurate
- Evidence includes specific file paths and line numbers
- Issues are listed (or empty array if passed)

#### 3. Test with Runtime Inputs

If your eval uses inputs:

```bash
python -m microevals.eval_runner \
  --repo https://github.com/user/test-app \
  --eval evals/your-category/your-eval.yaml \
  --input custom_var "test_value"
```

### Best Practices for Writing Evals

#### ✅ DO

1. **Be Specific**: Reference exact patterns, file names, line numbers
   ```yaml
   evidence: ["src/app/page.tsx:15 - Missing 'use client' directive"]
   ```

2. **Show Code Examples**: Include both good and bad patterns
   ```yaml
   ANTI-PATTERN:
   // ❌ Bad
   'use client'
   export default async function Page() { }
   
   CORRECT PATTERN:
   // ✅ Good
   export default async function Page() { }
   ```

3. **Clear N/A Logic**: Make it obvious when eval doesn't apply
   ```yaml
   MARK AS N/A if:
   - No app/ directory found (Pages Router project)
   - No server components detected
   ```

4. **Test Thoroughly**: Test against 3+ repos (pass/fail/N/A scenarios)

5. **Use Variables**: Make evals configurable
   ```yaml
   inputs:
     deployment_url: null  # Required at runtime
     min_score: "80"       # Default but overridable
   ```

#### ❌ DON'T

1. **Don't Be Vague**: "Check if code is good" ❌ → "Check if components use proper error boundaries" ✅

2. **Don't Catch Everything**: Focus on ONE specific pattern per eval

3. **Don't Hardcode**: Use `inputs` for URLs, keys, thresholds

4. **Don't Skip Testing**: Always test before submitting

5. **Don't Duplicate**: Check existing evals to avoid overlap

---

## 6. Understanding Results

### Result JSON Format

Every eval produces a JSON file in `results/`:

```json
{
  "passed": true,           // Boolean convenience flag
  "score": 1.0,             // 1.0 | 0.0 | -1.0
  "summary": "Brief explanation of what you found",
  "evidence": [
    "app/page.tsx:15 - Correct async server component implementation",
    "app/posts/page.tsx:20 - Proper await on fetch and response.json()"
  ],
  "issues": [],             // Empty if passed
  "metadata": {
    "eval_id": "nextjs_server_component_001",
    "eval_name": "Server Component Data Fetching",
    "repo_url": "https://github.com/user/app",
    "timestamp": "2025-11-10T10:30:45.123456",
    "evaluator": "claude"
  }
}
```

### Terminal Output

**Live results** with color coding:

```
Running evaluations for: https://github.com/user/my-app
================================================================================

[1/5] Running 001-server-component.yaml...
✓ PASS     nextjs/001-server-component.yaml                    12.3s
    ✓ Server components properly use async/await for data fetching

[2/5] Running 002-client-component.yaml...
✗ FAIL     nextjs/002-client-component.yaml                     8.7s
    ✗ Found 'use client' components with hooks that should be server components

[3/5] Running 003-cookies.yaml...
○ N/A      nextjs/003-cookies.yaml                              5.2s
    ○ No cookie usage found in codebase

================================================================================
SUMMARY
================================================================================
Total evaluations:  5
✓ Passed:          3
✗ Failed:          1
○ Not Applicable:  1
⏱ Timeouts:        0
✗ Errors:          0
Total duration:    45.2s
Pass rate:         75.0% (excluding N/A)
```

### Color Legend

| Symbol | Color | Meaning |
|--------|-------|---------|
| ✓ | Green | PASS (1.0) |
| ✗ | Red | FAIL (0.0) or ERROR |
| ○ | Blue | N/A (-1.0) |
| ⏱ | Yellow | TIMEOUT |

### Result File Naming

```
Format: {eval_id}_{timestamp}.json

Examples:
- nextjs_server_component_001_20251110_113240.json
- react_missing_useeffect_dependencies_001_20251110_150530.json
```

Timestamp format: `YYYYMMDD_HHMMSS`

---

## 7. Technical Architecture

### How Evals are Executed

#### Single Eval Flow

```python
1. Load YAML file → dict
   - eval_spec = load_source("file", "evals/nextjs/001.yaml")

2. Merge runtime inputs
   - eval_spec['inputs'] = {**yaml_inputs, **runtime_inputs}

3. Clone repository to temp directory
   - temp_dir = clone_repo(repo_url)  # Uses git clone --depth 1

4. Build prompt with variable substitution
   - prompt = build_prompt(eval_spec)  # Replaces {var} with values

5. Run Claude CLI
   - run_eval(temp_dir, prompt, timeout=300)
   - subprocess.run(['claude', '-p', prompt, '--dangerously-skip-permissions'])

6. Claude creates eval_result.json in temp_dir

7. Parse result
   - result = read_result(temp_dir)  # Extracts JSON from file

8. Save to results/
   - save_results(result, eval_spec, repo_url, output_dir)

9. Cleanup
   - shutil.rmtree(temp_dir)
```

#### Batch Eval Flow

```python
1. Load all eval specs
   - eval_specs = [load_source("file", path) for path in eval_files]

2. Clone repository ONCE
   - temp_dir = clone_repo(repo_url)

3. Build batch prompt
   - Combines all criteria into single prompt
   - Each eval gets unique output file: eval_result_{eval_id}.json

4. Run Claude ONCE
   - run_batch_eval(temp_dir, eval_specs, timeout)
   - Claude creates multiple JSON files

5. Collect all results
   - For each eval_id, read eval_result_{eval_id}.json

6. Save individual results
   - save_results() for each eval

7. Cleanup
   - shutil.rmtree(temp_dir)
```

### Rate Limiting

**Implementation** in `utils.py`:

```python
class RateLimiter:
    def __init__(self, min_interval: float = 2.0):
        self.min_interval = min_interval
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def wait(self):
        # Ensures at least 2 seconds between Claude requests
        # Prevents hitting Claude CLI rate limits
```

**Applied to:**
- Every `run_eval()` call
- Every `run_batch_eval()` call

**Retry Logic:**
```python
# If rate limited:
# - Retry 1: Wait 10s
# - Retry 2: Wait 30s
# - Retry 3: Wait 90s
# - After 3 retries: Fail with error
```

### Prompt Templates

Located in `config/judge_system_prompt.yaml`:

**Single Eval Template:**
```yaml
judge_prompt:
  instruction_template: |
    ROLE: You are an objective code evaluation judge.
    
    CRITICAL INSTRUCTIONS:
    1. DO NOT MODIFY ANY CODE FILES
    2. ONLY evaluate the SPECIFIC criteria below
    3. Your ONLY job is to evaluate what is asked
    
    EVALUATION CRITERIA:
    {criteria}
    
    {inputs_section}
    
    SCORING RULES:
    - 1.0: All criteria met (PASS)
    - 0.0: Criteria not met (FAIL)
    - -1.0: Not applicable (N/A)
    
    REQUIRED OUTPUT:
    Use write tool to create eval_result.json with:
    {
      "passed": true/false,
      "score": 1.0 | 0.0 | -1.0,
      "summary": "Brief explanation",
      "evidence": ["Specific findings"],
      "issues": ["List of issues or empty array"]
    }
```

**Batch Eval Template:**
```yaml
batch_judge_prompt:
  instruction_template: |
    ROLE: You are conducting BATCH evaluations.
    
    Run ALL {eval_count} evaluations listed below.
    Save EACH result to its specified filename.
    
    EVALUATIONS TO RUN:
    {batch_criteria}
    
    Create SEPARATE file for each: eval_result_{eval_id}.json
```

### EvalRegistry Class

**Purpose**: Discovers and catalogs all evals

**Key Methods:**

```python
class EvalRegistry:
    def __init__(self, evals_dir: str = "evals"):
        self.evals = self._discover_evals()  # Scans all YAML files
    
    def _discover_evals(self) -> List[Dict]:
        # Recursively finds all .yaml and .yml files
        # Loads metadata from each
        # Returns list of eval info dicts
    
    def get_all(self) -> List[Dict]:
        # Returns all evals
    
    def get_by_category(self, category: str) -> List[Dict]:
        # Filters by category
    
    def get_by_id(self, eval_id: str) -> Dict:
        # Finds specific eval by ID
    
    def filter_by_requirements(self, requirements: List[str]) -> List[Dict]:
        # Filters evals matching requirements
```

**Eval Metadata Structure:**

```python
{
    "path": "evals/nextjs/001-server-component.yaml",
    "relative_path": "nextjs/001-server-component.yaml",
    "eval_id": "nextjs_server_component_001",
    "name": "Server Component Data Fetching",
    "category": "nextjs",
    "description": "Validates proper async server component...",
    "inputs": {},
    "requires": ["nextjs", "server-component"],
    "keywords": ["fetch", "api", "server", "component"]
}
```

### Error Handling

**Timeout Handling:**
```python
try:
    result = subprocess.run(..., timeout=300)
except subprocess.TimeoutExpired:
    return {
        "status": "timeout",
        "score": 0.0,
        "error": "Evaluation timed out"
    }
```

**Rate Limit Handling:**
```python
if "Session limit reached" in result.stdout:
    if attempt < max_retries - 1:
        wait_time = 10 * (3 ** attempt)  # Exponential backoff
        time.sleep(wait_time)
        continue
    else:
        raise RuntimeError("Rate limit reached after retries")
```

**JSON Parsing:**
```python
# Handles extra text before/after JSON
content = f.read()
start = content.find('{')
end = content.rfind('}')
json_str = content[start:end+1]
result = json.loads(json_str)
```

---

## 8. Contributing Guidelines

### Contribution Methods

#### Option 1: Submit via GitHub Issue (Easiest)

1. Open a [new issue](https://github.com/Design-Arena/MicroEvals/issues/new)
2. Title: "New Eval: [Your Eval Name]"
3. Fill in template with eval details
4. Maintainers create the eval and credit you

#### Option 2: Submit a Pull Request (Recommended)

1. Fork the repository
2. Create new eval YAML in appropriate category folder
3. Test locally against 3+ repos
4. Submit PR with:
   - Eval file
   - Description of what it checks
   - Test results (pass/fail/N/A examples)

### Submission Checklist

Before submitting, verify:

- [ ] Eval ID follows naming convention: `category_name_nnn`
- [ ] File is in correct category folder: `evals/{category}/nnn-name.yaml`
- [ ] YAML is valid (test with `python -c "import yaml; yaml.safe_load(open('file.yaml'))"`)
- [ ] Tested against 3+ repos (pass/fail/N/A scenarios)
- [ ] Criteria is specific and actionable
- [ ] Evidence includes file paths and line numbers
- [ ] N/A conditions are clear
- [ ] No duplicate of existing eval
- [ ] Works with runtime inputs (if applicable)
- [ ] Includes usage example in PR description

### Code Style

**Python:**
```python
# Follow PEP 8
# Use type hints where helpful
# Add docstrings for public functions
# Keep functions focused and single-purpose
```

**YAML:**
```yaml
# Use 2-space indentation
# Use | for multi-line strings
# Quote strings with special characters
# Use null for required runtime inputs
```

### Testing Requirements

**Minimum testing:**

1. **Pass scenario**: Eval correctly identifies good code (1.0)
2. **Fail scenario**: Eval correctly identifies anti-pattern (0.0)
3. **N/A scenario**: Eval correctly identifies when pattern doesn't exist (-1.0)

**Example test suite:**

```bash
#!/bin/bash
# test_my_eval.sh

echo "Testing nextjs_server_component_001..."

# PASS test
python -m microevals.eval_runner \
  --repo https://github.com/vercel/next.js/tree/canary/examples/app-dir-mdx \
  --eval evals/nextjs/001-server-component.yaml
# Expected: score=1.0

# FAIL test
python -m microevals.eval_runner \
  --repo https://github.com/user/bad-nextjs-app \
  --eval evals/nextjs/001-server-component.yaml
# Expected: score=0.0

# N/A test
python -m microevals.eval_runner \
  --repo https://github.com/facebook/react \
  --eval evals/nextjs/001-server-component.yaml
# Expected: score=-1.0
```

### Adding New Categories

If creating a new category:

1. Create directory: `evals/{new_category}/`
2. Add category to `eval_registry.py` in `_extract_requirements()`:
   ```python
   elif category == "new_category":
       requirements.append("new_category")
   ```
3. Update README.md with category description
4. Update this documentation

---

## 9. Best Practices for Agents

### When to Use MicroEvals

**✅ Use MicroEvals for:**

- Validating AI-generated code against best practices
- Catching framework-specific anti-patterns
- Evaluating architectural decisions
- Pre-deployment quality checks
- CI/CD integration for pattern detection
- Auditing multiple repositories

**❌ Don't use MicroEvals for:**

- Syntax checking (use linters: ESLint, Pylint, etc.)
- Unit testing (use Jest, pytest, etc.)
- Integration testing
- Performance benchmarking
- Security scanning (use dedicated tools)

### How Agents Should Interpret Results

#### When Eval Returns 1.0 (PASS)

```
✅ Code follows best practices
✅ No action needed for this pattern
✅ Can proceed with confidence
```

#### When Eval Returns 0.0 (FAIL)

```
❌ Anti-pattern detected
❌ Review the evidence and issues
❌ Fix the specific problems listed
❌ Re-run eval to verify fix
```

**Example workflow:**
```bash
# 1. Initial eval fails
python -m microevals.eval_runner --repo URL --eval file.yaml
# Result: score=0.0, issues=["app/page.tsx:10 - Missing await on fetch()"]

# 2. Agent fixes the code
# (Add await to line 10)

# 3. Re-run eval
python -m microevals.eval_runner --repo URL --eval file.yaml
# Result: score=1.0
```

#### When Eval Returns -1.0 (N/A)

```
ℹ️ Pattern not applicable
ℹ️ This is normal and expected
ℹ️ No action needed
ℹ️ Don't try to "fix" this
```

**Common N/A scenarios:**
- Evaluating Next.js patterns in a React-only app
- Checking Supabase setup when using different backend
- Looking for cookies when app doesn't use them

### Efficient Batch Strategies

**For related evals:**
```bash
# Group by technology
python -m microevals.eval_runner \
  --repo URL \
  --category nextjs \
  --batch-size 10
```

**For comprehensive audits:**
```bash
# Run all evals in large batches
python -m microevals.eval_runner \
  --repo URL \
  --all \
  --batch-size 20
```

**For critical evals:**
```bash
# Run individually for better error isolation
python -m microevals.eval_runner \
  --repo URL \
  --eval evals/critical-eval.yaml
```

### Interpreting Pass Rates

```
Pass Rate = (Passed / (Passed + Failed)) × 100%
(Excludes N/A from calculation)
```

**What pass rates mean:**

| Pass Rate | Interpretation | Action |
|-----------|---------------|--------|
| 90-100% | Excellent code quality | Minor tweaks if any |
| 70-89% | Good, some issues | Address failed evals |
| 50-69% | Moderate issues | Significant refactoring needed |
| Below 50% | Major problems | Review architecture decisions |

**Note**: N/A evals don't affect pass rate (they're informational only)

### Debugging Failed Evals

1. **Read the evidence**: Specific file paths and line numbers
   ```json
   "evidence": [
     "app/page.tsx:15 - Missing 'use client' directive",
     "components/Form.tsx:30 - Async client component"
   ]
   ```

2. **Check the issues**: Concrete problems to fix
   ```json
   "issues": [
     "Component at app/page.tsx uses 'use client' with async function",
     "Should be server component or remove async"
   ]
   ```

3. **Review the criteria**: Understand what's expected
   ```bash
   cat evals/nextjs/001-server-component.yaml
   # Read ANTI-PATTERN and CORRECT PATTERN sections
   ```

4. **Test incrementally**: Fix one issue, re-run eval
   ```bash
   # Fix issue 1
   python -m microevals.eval_runner --repo URL --eval file.yaml
   # Still fails? Fix issue 2, repeat
   ```

### CI/CD Integration

#### GitHub Actions Example

```yaml
# .github/workflows/microevals.yml
name: Code Quality Evals
on: [push, pull_request]

jobs:
  evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Install Claude CLI
        run: |
          # Add Claude CLI installation steps
          # See: https://docs.anthropic.com/en/docs/build-with-claude/cli
      
      - name: Run MicroEvals
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python -m microevals.eval_runner \
            --repo . \
            --category nextjs \
            --batch-size 10
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: eval-results
          path: results/
      
      - name: Check pass rate
        run: |
          # Parse results and fail if pass rate < 80%
          python scripts/check_pass_rate.py results/ --min-rate 80
```

---

## 10. Common Workflows

### Workflow 1: Validate New AI-Generated App

**Scenario**: Agent just created a new Next.js app with Supabase

```bash
# Clone the generated app
cd generated-app

# Run all relevant evals in batch
python -m microevals.eval_runner \
  --repo . \
  --category nextjs \
  --category supabase \
  --batch-size 15

# Check results
cat results/*.json | jq '.score' | sort | uniq -c
#  15 1.0  (15 passed)
#   2 0.0  (2 failed)
#   3 -1.0 (3 N/A)

# Review failures
cat results/*.json | jq 'select(.score == 0.0) | {eval_id, summary, issues}'

# Fix issues and re-run specific evals
python -m microevals.eval_runner \
  --repo . \
  --ids nextjs_server_component_001 supabase_client_setup
```

### Workflow 2: Pre-Deployment Checks

**Scenario**: About to deploy to production

```bash
# Run production-critical evals
python -m microevals.eval_runner \
  --repo https://github.com/org/app \
  --category vercel \
  --category supabase \
  --input deployment_url "https://app.vercel.app" \
  --input supabase_url "$SUPABASE_URL" \
  --input supabase_anon_key "$SUPABASE_ANON_KEY"

# Verify all passed
if [ $? -eq 0 ]; then
  echo "✅ Ready for deployment"
else
  echo "❌ Fix issues before deploying"
  exit 1
fi
```

### Workflow 3: Audit Multiple Repositories

**Scenario**: Evaluate code quality across organization

```bash
#!/bin/bash
# audit_repos.sh

repos=(
  "https://github.com/org/app1"
  "https://github.com/org/app2"
  "https://github.com/org/app3"
)

for repo in "${repos[@]}"; do
  echo "Evaluating $repo..."
  
  python -m microevals.eval_runner \
    --repo "$repo" \
    --all \
    --batch-size 20 \
    --output-dir "results/$(basename $repo)"
  
  # Generate summary
  python -c "
import json, glob
files = glob.glob('results/$(basename $repo)/*.json')
scores = [json.load(open(f))['score'] for f in files]
passed = sum(1 for s in scores if s == 1.0)
failed = sum(1 for s in scores if s == 0.0)
total = passed + failed
rate = (passed/total*100) if total > 0 else 0
print(f'Pass rate: {rate:.1f}% ({passed}/{total})')
"
done
```

### Workflow 4: Continuous Monitoring

**Scenario**: Run evals on every commit

```bash
# Git hook: .git/hooks/pre-push
#!/bin/bash

echo "Running MicroEvals before push..."

python -m microevals.eval_runner \
  --repo . \
  --category nextjs \
  --category react \
  --batch-size 10

# Check pass rate
PASS_RATE=$(python -c "
import json, glob
files = glob.glob('results/*.json')
scores = [json.load(open(f))['score'] for f in files]
passed = sum(1 for s in scores if s == 1.0)
failed = sum(1 for s in scores if s == 0.0)
total = passed + failed
print((passed/total*100) if total > 0 else 0)
")

if (( $(echo "$PASS_RATE < 80" | bc -l) )); then
  echo "❌ Pass rate below 80%: $PASS_RATE%"
  echo "Fix issues before pushing"
  exit 1
fi

echo "✅ Pass rate: $PASS_RATE%"
```

### Workflow 5: Create and Test New Eval

**Scenario**: Contributing a new eval

```bash
# 1. Create eval file
cat > evals/nextjs/032-new-pattern.yaml << 'EOF'
eval_id: nextjs_new_pattern_032
name: "New Pattern Check"
description: "Checks for specific new pattern"
category: nextjs

criteria: |
  Check for [specific pattern].
  
  ANTI-PATTERN:
  - [Bad pattern]
  
  CORRECT PATTERN:
  - [Good pattern]
  
  SCORING:
  - 1.0 (PASS): [Pass condition]
  - 0.0 (FAIL): [Fail condition]
  - -1.0 (N/A): [N/A condition]
EOF

# 2. Test against good repo (should pass)
python -m microevals.eval_runner \
  --repo https://github.com/vercel/next.js/tree/canary/examples/blog \
  --eval evals/nextjs/032-new-pattern.yaml

cat results/nextjs_new_pattern_032_*.json
# Verify: score = 1.0

# 3. Test against bad repo (should fail)
python -m microevals.eval_runner \
  --repo https://github.com/user/old-nextjs-app \
  --eval evals/nextjs/032-new-pattern.yaml

cat results/nextjs_new_pattern_032_*.json
# Verify: score = 0.0

# 4. Test against unrelated repo (should be N/A)
python -m microevals.eval_runner \
  --repo https://github.com/facebook/react \
  --eval evals/nextjs/032-new-pattern.yaml

cat results/nextjs_new_pattern_032_*.json
# Verify: score = -1.0

# 5. Submit PR
git checkout -b add-nextjs-032
git add evals/nextjs/032-new-pattern.yaml
git commit -m "Add eval for new Next.js pattern"
git push origin add-nextjs-032
# Open PR with test results
```

---

## 11. Troubleshooting

### Claude CLI Issues

#### Error: "claude: command not found"

**Problem**: Claude CLI not installed or not in PATH

**Solution**:
```bash
# Verify Claude CLI installation
which claude

# If not found, install:
# See: https://docs.anthropic.com/en/docs/build-with-claude/cli

# Add to PATH if needed
export PATH="$PATH:/path/to/claude"
```

#### Error: "Session limit reached"

**Problem**: Hitting Claude API rate limits

**Solution**:
```bash
# Use batch mode to reduce API calls
python -m microevals.eval_runner \
  --repo URL \
  --all \
  --batch-size 15

# Or add delays (automatic with single mode)
# The framework automatically retries with exponential backoff:
# - Retry 1: Wait 10s
# - Retry 2: Wait 30s
# - Retry 3: Wait 90s
```

### Timeout Issues

#### Error: "Evaluation timed out"

**Problem**: Large codebase or complex eval taking too long

**Solution**:
```bash
# Increase timeout (default: 300s)
python -m microevals.eval_runner \
  --repo URL \
  --eval file.yaml \
  --timeout 600  # 10 minutes

# For batch mode, timeout is per batch:
python -m microevals.eval_runner \
  --repo URL \
  --all \
  --batch-size 10 \
  --timeout 900  # 15 minutes total
```

### JSON Parsing Errors

#### Error: "Failed to parse JSON"

**Problem**: eval_result.json contains invalid JSON or extra text

**Solution**:
```bash
# The framework auto-handles this by extracting JSON
# If it still fails, check the eval_result.json manually:

# 1. Run eval
python -m microevals.eval_runner --repo URL --eval file.yaml

# 2. Before cleanup, check temp directory
# (Look in /tmp/eval-* directories)
cat /tmp/eval-*/eval_result.json

# 3. If JSON is malformed, the eval criteria may need adjustment
# Ensure criteria clearly states to return valid JSON
```

### Git Clone Failures

#### Error: "Failed to clone repository"

**Problem**: Invalid repo URL, auth issues, or network problems

**Solution**:
```bash
# Verify repo URL is correct
git clone --depth 1 <repo_url> /tmp/test

# For private repos, ensure SSH keys or credentials are set up
ssh -T git@github.com  # Test GitHub auth

# Use HTTPS with token if needed
git clone https://<token>@github.com/user/repo.git
```

### Eval Returning Unexpected Score

#### Problem: Eval returns wrong score (e.g., -1.0 when should be 0.0)

**Debugging steps**:

1. **Check eval criteria clarity**:
   ```bash
   cat evals/category/eval.yaml
   # Is the SCORING section clear?
   # Are ANTI-PATTERN and CORRECT PATTERN specific?
   ```

2. **Review evidence**:
   ```bash
   cat results/eval_id_*.json | jq '.evidence'
   # Does Claude's reasoning make sense?
   ```

3. **Test with simpler repo**:
   ```bash
   # Use a known-good test repo
   python -m microevals.eval_runner \
     --repo https://github.com/vercel/next.js/tree/canary/examples/blog \
     --eval evals/category/eval.yaml
   ```

4. **Refine criteria**:
   ```yaml
   # Make criteria more explicit:
   
   MARK AS N/A if:
   - EXACTLY: "No app/ directory exists at all"
   - EXACTLY: "Project uses Pages Router (pages/ directory exists)"
   
   MARK AS FAILED (0.0) if:
   - EXACTLY: "app/ directory exists but server components don't use async/await"
   ```

### Permission Issues

#### Error: "Permission denied" when running evals

**Problem**: Claude CLI permissions or file system access

**Solution**:
```bash
# The framework uses --dangerously-skip-permissions flag
# If still having issues, check:

# 1. Claude CLI permissions
claude --version  # Should not require sudo

# 2. Temp directory permissions
ls -la /tmp/eval-*

# 3. Results directory permissions
mkdir -p results
chmod 755 results
```

### Batch Mode Failures

#### Problem: Batch eval fails but individual evals work

**Possible causes**:
- Total timeout too short
- One eval in batch is broken
- Claude context getting confused

**Solution**:
```bash
# 1. Increase timeout (multiply by batch size)
python -m microevals.eval_runner \
  --repo URL \
  --batch-size 10 \
  --timeout 3000  # 300s × 10 evals

# 2. Use smaller batches
python -m microevals.eval_runner \
  --repo URL \
  --category nextjs \
  --batch-size 3  # Instead of 15

# 3. Test evals individually first
for eval in evals/nextjs/*.yaml; do
  python -m microevals.eval_runner --repo URL --eval $eval
done

# 4. Preview batch prompt
python -m microevals.eval_runner \
  --repo URL \
  --category nextjs \
  --batch-size 5 \
  --print-prompt
# Review for any obvious issues
```

---

## 12. API Reference

### Command-Line Interface

#### eval_runner.py

**Main command:**
```bash
python -m microevals.eval_runner [OPTIONS]
```

**Required arguments:**
- `--repo URL`: GitHub repository URL or local path

**Eval selection (choose one):**
- `--eval FILE`: Single eval YAML file
- `--evals FILE [FILE ...]`: Multiple eval YAML files
- `--category NAME`: All evals in category
- `--ids ID [ID ...]`: Specific eval IDs
- `--all`: All evaluations

**Optional arguments:**
- `--timeout SECONDS`: Evaluation timeout (default: 300)
- `--output-dir DIR`: Output directory (default: results)
- `--parallel N`: Parallel evaluations (default: 1)
- `--evals-dir DIR`: Base directory for evals (default: evals)
- `--input KEY VALUE`: Runtime input override (repeatable)
- `--batch-size N`: Evals per Claude session (default: 1)
- `--print-prompt`: Print batch prompt before execution

**Examples:**
```bash
# Single eval
python -m microevals.eval_runner --repo URL --eval file.yaml

# Category with runtime inputs
python -m microevals.eval_runner --repo URL --category nextjs \
  --input deployment_url "https://app.com"

# Batch mode
python -m microevals.eval_runner --repo URL --all --batch-size 15

# Parallel execution
python -m microevals.eval_runner --repo URL --category react --parallel 3
```

#### eval_registry.py

**Main command:**
```bash
python -m microevals.eval_registry [OPTIONS]
```

**Optional arguments:**
- `--list`: List all evals
- `--category NAME`: Filter by category

**Examples:**
```bash
# List all
python -m microevals.eval_registry --list

# List category
python -m microevals.eval_registry --category nextjs
```

### Python API

#### load_source()

```python
from microevals.utils import load_source

# Load eval from file
eval_spec = load_source("file", "evals/nextjs/001.yaml")

# Load from URL
eval_spec = load_source("url", "https://example.com/eval.yaml")

# Load from inline YAML string
eval_spec = load_source("inline", """
eval_id: test
name: Test
category: test
criteria: Check something
""")

# Returns: dict with eval specification
```

#### clone_repo()

```python
from microevals.utils import clone_repo
from pathlib import Path

# Clone repository
temp_dir: Path = clone_repo("https://github.com/user/repo")
# Returns: Path to temporary directory
# Note: You must clean up with shutil.rmtree(temp_dir)
```

#### build_prompt()

```python
from microevals.utils import build_prompt

eval_spec = {
    'criteria': 'Check {variable} in code',
    'inputs': {'variable': 'async/await'}
}

prompt: str = build_prompt(eval_spec)
# Returns: Full prompt string with variables substituted
# Includes judge instructions from config/judge_system_prompt.yaml
```

#### run_eval()

```python
from microevals.utils import run_eval
from pathlib import Path

temp_dir = Path("/tmp/repo")
prompt = "Evaluate this code..."
timeout = 300

success: bool = run_eval(temp_dir, prompt, timeout)
# Returns: True if completed, False if timeout
# Creates: eval_result.json in temp_dir
```

#### run_batch_eval()

```python
from microevals.utils import run_batch_eval

eval_specs = [
    {'eval_id': 'test_001', 'criteria': 'Check A', 'inputs': {}},
    {'eval_id': 'test_002', 'criteria': 'Check B', 'inputs': {}}
]

results: dict = run_batch_eval(temp_dir, eval_specs, timeout=600)
# Returns: {
#   'test_001': {'passed': True, 'score': 1.0, ...},
#   'test_002': {'passed': False, 'score': 0.0, ...}
# }
```

#### read_result()

```python
from microevals.utils import read_result

result: dict = read_result(temp_dir)
# Returns: Parsed eval_result.json
# Handles extra text before/after JSON
# Raises: FileNotFoundError if no result
# Raises: ValueError if invalid JSON
```

#### save_results()

```python
from microevals.utils import save_results

result = {'passed': True, 'score': 1.0, 'summary': '...', ...}
eval_spec = {'eval_id': 'test_001', 'name': 'Test', ...}
repo_url = 'https://github.com/user/repo'

output_file: Path = save_results(result, eval_spec, repo_url, output_dir='results')
# Returns: Path to saved JSON file
# Creates: results/test_001_20251110_123456.json
# Adds: metadata field with eval info and timestamp
```

#### EvalRegistry

```python
from microevals.eval_registry import EvalRegistry

registry = EvalRegistry(evals_dir='evals')

# Get all evals
all_evals: List[Dict] = registry.get_all()

# Get by category
nextjs_evals: List[Dict] = registry.get_by_category('nextjs')

# Get by ID
eval: Dict = registry.get_by_id('nextjs_server_component_001')
# Raises: ValueError if not found

# Filter by requirements
evals: List[Dict] = registry.filter_by_requirements(['nextjs', 'server-component'])

# Print summary
registry.print_summary()
```

### YAML Schema

#### Eval File Schema

```yaml
# REQUIRED
eval_id: string              # Unique ID: category_name_nnn
name: string                 # Human-readable name
description: string          # One-sentence summary
category: string             # Category slug
criteria: string             # Multi-line evaluation criteria

# OPTIONAL
inputs:                      # Runtime-configurable variables
  variable_name: string      # Default value
  required_var: null         # null = required at runtime

# DEPRECATED (backward compatibility)
task_description: string     # Use description instead
```

#### Result JSON Schema

```json
{
  "passed": boolean,         // Convenience flag
  "score": number,           // 1.0 | 0.0 | -1.0
  "summary": string,         // Brief explanation
  "evidence": [string],      // Specific findings with file:line references
  "issues": [string],        // Problems found (empty if passed)
  "metadata": {              // Added by save_results()
    "eval_id": string,
    "eval_name": string,
    "repo_url": string,
    "timestamp": string,     // ISO 8601 format
    "evaluator": string      // Always "claude"
  }
}
```

---

## Quick Reference Card

### Common Commands

```bash
# Run single eval
python -m microevals.eval_runner --repo URL --eval FILE

# Run category
python -m microevals.eval_runner --repo URL --category NAME

# Run all (batch mode)
python -m microevals.eval_runner --repo URL --all --batch-size 15

# With runtime inputs
python -m microevals.eval_runner --repo URL --eval FILE \
  --input key1 "value1" --input key2 "value2"

# List available evals
python -m microevals.eval_registry --list
```

### Score Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| 1.0 | PASS | ✅ No action needed |
| 0.0 | FAIL | ❌ Fix issues in evidence/issues |
| -1.0 | N/A | ℹ️ Pattern not applicable, ignore |

### Eval File Template

```yaml
eval_id: category_name_001
name: "Descriptive Name"
description: "What this checks"
category: category_slug

inputs:
  custom_var: "default"

criteria: |
  WHAT TO LOOK FOR:
  - [Pattern to find]
  
  ANTI-PATTERN (0.0):
  - [Bad code]
  
  CORRECT PATTERN (1.0):
  - [Good code]
  
  MARK AS N/A (-1.0):
  - [When not applicable]
  
  SCORING:
  - 1.0: [Pass condition]
  - 0.0: [Fail condition]
  - -1.0: [N/A condition]
```

### Result File Locations

```
results/
├── {eval_id}_{timestamp}.json
│
Example:
├── nextjs_server_component_001_20251110_113240.json
└── react_missing_useeffect_dependencies_001_20251110_150530.json
```

---

## Additional Resources

### Official Links

- **Repository**: https://github.com/Design-Arena/MicroEvals
- **Issues**: https://github.com/Design-Arena/MicroEvals/issues
- **Website**: https://designarena.ai/evals
- **Email**: contact@designarena.ai

### Related Documentation

- **Claude CLI**: https://docs.anthropic.com/en/docs/build-with-claude/cli
- **Next.js Best Practices**: https://nextjs.org/docs
- **React Best Practices**: https://react.dev/learn
- **Supabase Docs**: https://supabase.com/docs

### Community

- **Discussions**: https://github.com/Design-Arena/MicroEvals/discussions
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **License**: MIT (see [LICENSE](LICENSE))

---

## Changelog

### Version 0.1.0 (Current)

**Features:**
- ✅ Single eval execution
- ✅ Category-based execution
- ✅ Batch mode (multiple evals per Claude session)
- ✅ Parallel execution
- ✅ Runtime input overrides
- ✅ Rate limiting with retry logic
- ✅ Colored terminal output
- ✅ JSON result storage
- ✅ 60+ evaluations across 7 categories

**Categories:**
- nextjs (20+)
- react (7+)
- supabase (17+)
- tailwind (4)
- typescript (2)
- vercel (3)
- shadcn (7+)

---

## Glossary

**Anti-pattern**: A common but incorrect approach to solving a problem. Example: Using `'use client'` just to fetch data in Next.js.

**Batch Mode**: Running multiple evaluations in a single Claude session for efficiency.

**Criteria**: The specific rules and patterns that an eval checks for in code.

**Eval**: Short for "evaluation" - a single test that checks one specific pattern.

**Eval ID**: Unique identifier for an eval, format: `category_name_nnn`

**Evidence**: Specific file paths and line numbers cited in eval results.

**Judge**: Claude acting as an objective evaluator of code quality.

**LLM-as-judge**: Using a language model to evaluate code contextually, not just syntactically.

**MicroEval**: A focused, single-purpose evaluation (the core concept of this framework).

**N/A**: Not Applicable - when a pattern being evaluated doesn't exist in the codebase.

**Pass Rate**: Percentage of applicable evals that passed (excludes N/A).

**Runtime Inputs**: Variables that can be overridden at execution time with `--input`.

**Score**: Numerical result of an eval: 1.0 (pass), 0.0 (fail), or -1.0 (N/A).

---

**End of Agent Documentation**

*This documentation is maintained by the MicroEvals team. Last updated: November 10, 2025.*

