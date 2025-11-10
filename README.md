# MicroEvals

**Automated evaluation framework for AI-generated code quality and best practices.**

MicroEvals is a collection of focused, automated tests that evaluate whether AI-generated code (or any codebase) follows framework-specific best practices and avoids common anti-patterns. Each evaluation uses Claude to analyze your codebase against specific criteria.

## What Are MicroEvals?

MicroEvals are **micro-evaluations** - small, focused tests that check for specific patterns or anti-patterns in your code. Unlike traditional linters that check syntax, MicroEvals use LLM as a judge to understand context and evaluate architectural decisions.

**Example Use Cases:**
- Verify Next.js App Router best practices (server components, data fetching)
- Catch React anti-patterns (missing dependencies, incorrect hooks usage)
- Validate Supabase security (RLS policies, proper auth setup)
- Check TypeScript type safety (unsafe assertions, missing null checks)
- Ensure proper shadcn/ui integration
- Audit deployment configurations

## Quick Start

### Installation

#### Option 1: Install from PyPI (Recommended)

```bash
pip install microevals
```

#### Option 2: Install from Source (For Development)

```bash
# Clone the repository
git clone https://github.com/Design-Arena/MicroEvals
cd MicroEvals

# Install in development mode
pip install -e .
```

### Prerequisites

1. **Python 3.8+** installed
2. **Claude CLI** installed and authenticated:
   ```bash
   # Install Claude CLI (if not already installed)
   # See: https://docs.anthropic.com/en/docs/build-with-claude/cli
   
   # Verify installation
   claude --version
   
   # If command not found, add Claude to your PATH:
   export PATH="$PATH:/path/to/claude"
   # Add the export line to your ~/.bashrc or ~/.zshrc to make it permanent
   ```

3. **Git** installed (for remote repositories)

### Run Your First Eval

```bash
# Navigate to your project
cd your-nextjs-app

# Run evaluations on current directory
microeval --category nextjs

# Check the results
cat results/*.json
```

**🔒 Safety Note:** When running on local directories, your code is **copied** to a temporary directory before evaluation. Your original files are **never modified or deleted**. The framework has 6 independent safety checks to prevent accidental file deletion.

### Alternative: Run Against Remote Repository

```bash
# Run against a GitHub repository
microeval --repo https://github.com/user/app --category nextjs
```

## Available Eval Categories

| Category | Count | Description |
|----------|-------|-------------|
| **nextjs** | 20+ | Next.js App Router patterns, server/client components, routing |
| **react** | 7+ | React hooks, state management, component patterns |
| **supabase** | 17+ | Supabase auth, database, storage, RLS security |
| **tailwind** | 4+ | Tailwind CSS configuration and usage |
| **typescript** | 2+ | TypeScript type safety and best practices |
| **vercel** | 3+ | Vercel deployment and configuration |
| **shadcn** | 7+ | shadcn/ui component library integration |

**See all available evals:**
```bash
# List all evals (recommended)
microeval --list

# List evals in a specific category
microeval --list --category nextjs

# Or using Python module
python -m microevals.eval_registry --list
```

## Running Evals

### Local Directory (Recommended)

Run evaluations on your current project:

```bash
# Using the microeval command (recommended)
microeval --category nextjs

# Or using Python module directly
python -m microevals.eval_runner --category nextjs
```

**More examples:**

```bash
# Run a specific eval
microeval --eval evals/nextjs/001-server-component.yaml

# Run all evals
microeval --all

# Run with batch mode for speed
microeval --category nextjs --batch-size 10
```

### Remote Repository

Run evaluations against a GitHub repository:

```bash
# Using the microeval command
microeval --repo https://github.com/user/app --category nextjs

# Or using Python module directly
python -m microevals.eval_runner --repo https://github.com/user/app --category nextjs
```

**More examples:**

```bash
# Run specific eval
microeval --repo https://github.com/user/app --eval evals/nextjs/001-server-component.yaml

# Run all evals
microeval --repo https://github.com/user/app --all

# Run with batch mode
microeval --repo https://github.com/user/app --all --batch-size 15
```

### Specific Eval IDs

Run evaluations by their IDs:

```bash
# Using microeval command
microeval --ids nextjs_server_component_001 react_missing_useeffect_dependencies_001

# Or using Python module
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --ids nextjs_server_component_001 react_missing_useeffect_dependencies_001
```

### Multiple Specific Evals

Run multiple specific eval files:

```bash
# Using microeval command
microeval --evals evals/nextjs/001-server-component.yaml evals/react/001_missing_useeffect_dependencies.yaml

# Or using Python module
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --evals evals/nextjs/001-server-component.yaml evals/react/001_missing_useeffect_dependencies.yaml
```

## Advanced Usage

### Runtime Input Overrides

Override default values from eval YAML files:

```bash
# Using microeval command
microeval --eval evals/supabase/001_client_setup.yaml \
  --input supabase_url "https://xyz.supabase.co" \
  --input supabase_anon_key "your_key_here"

# Or using Python module
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --eval evals/supabase/001_client_setup.yaml \
  --input supabase_url "https://xyz.supabase.co" \
  --input supabase_anon_key "your_key_here"
```

### Parallel Execution

Run multiple evals in parallel (faster but uses more resources):

```bash
# Using microeval command
microeval --category nextjs --parallel 3

# Or using Python module
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --category nextjs \
  --parallel 3
```

### Batch Mode

Run multiple evals in a single Claude session (most efficient):

```bash
# Using microeval command - Run 5 evals per Claude session
microeval --category tailwind --batch-size 5

# Run all evals in large batches
microeval --all --batch-size 15

# Or using Python module
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --category tailwind \
  --batch-size 5
```

**Batch mode benefits:**
- Faster execution (single context for multiple evals)
- More efficient Claude usage
- Better for related evaluations

**Preview batch prompt before running:**

```bash
microeval --category tailwind --batch-size 3 --print-prompt

# Or using Python module
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --category tailwind \
  --batch-size 3 \
  --print-prompt
```

### Custom Timeout

Increase timeout for slower evaluations:

```bash
# Using microeval command
microeval --eval evals/nextjs/030_app_router_migration.yaml --timeout 600

# Or using Python module
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --eval evals/nextjs/030_app_router_migration.yaml \
  --timeout 600  # 10 minutes
```

### Custom Output Directory

Save results to a specific directory:

```bash
# Using microeval command
microeval --category nextjs --output-dir my_results

# Or using Python module
python -m microevals.eval_runner \
  --repo https://github.com/user/app \
  --category nextjs \
  --output-dir my_results
```

## Understanding Results

### Score System

Each eval returns a score:

| Score | Status | Meaning |
|-------|--------|---------|
| **1.0** | PASS | Code follows best practices, no issues found |
| **0.0** | FAIL | Anti-pattern detected or criteria not met |
| **-1.0** | N/A | Pattern/feature not present in codebase |

### Result Output

Results are saved to `results/` as JSON files:

```json
{
  "passed": true,
  "score": 1.0,
  "summary": "Server components properly use async/await for data fetching",
  "evidence": [
    "app/page.tsx:15 - Correct async server component implementation",
    "app/posts/page.tsx:20 - Proper await on fetch and response.json()"
  ],
  "issues": [],
  "metadata": {
    "eval_id": "nextjs_server_component_001",
    "eval_name": "Server Component Data Fetching",
    "repo_url": "https://github.com/user/app",
    "timestamp": "2025-11-10T10:30:45",
    "evaluator": "claude"
  }
}
```

### Terminal Output

Live results show in terminal with color coding:

```
Running evaluations for: https://github.com/user/my-app
================================================================================

[1/5] Running 001-server-component.yaml...
PASS     nextjs/001-server-component.yaml                    12.3s
    Server components properly use async/await for data fetching

[2/5] Running 002-client-component.yaml...
FAIL     nextjs/002-client-component.yaml                     8.7s
    Found 'use client' components with hooks that should be server components

[3/5] Running 003-cookies.yaml...
N/A      nextjs/003-cookies.yaml                              5.2s
    No cookie usage found in codebase

================================================================================
SUMMARY
================================================================================
Total evaluations:  5
Passed:            3
Failed:            1
Not Applicable:    1
Timeouts:          0
Errors:            0
Total duration:    45.2s
Pass rate:         75.0% (excluding N/A)
```

## Project Structure

```
MicroEvals/
├── microevals/                     # Main package
│   ├── __init__.py                 # Package initialization
│   ├── eval_runner.py              # Main CLI for running evals
│   ├── eval_registry.py            # Registry and discovery of evals
│   └── utils.py                    # Utility functions
│
├── evals/                          # Evaluation definitions
│   ├── nextjs/                     # Next.js-specific evals
│   │   ├── 001-server-component.yaml
│   │   ├── 002-client-component.yaml
│   │   └── ...
│   ├── react/                      # React-specific evals
│   ├── supabase/                   # Supabase-specific evals
│   ├── tailwind/                   # Tailwind-specific evals
│   ├── typescript/                 # TypeScript-specific evals
│   ├── vercel/                     # Vercel-specific evals
│   └── shadcn/                     # shadcn/ui-specific evals
│
├── config/                         # Configuration files
│   ├── judge_system_prompt.yaml    # Claude judge prompt templates
│   └── example_repos.json          # Example repositories
│
├── results/                        # Evaluation results (auto-generated)
│   └── *.json                      # Result files
│
├── requirements.txt                # Python dependencies
├── CONTRIBUTING.md                 # Contribution guidelines
├── LICENSE                         # License file
└── README.md                       # This file
```

## Creating Custom Evals

Want to add your own evaluations? See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Eval template and format
- Naming conventions
- Testing guidelines
- Submission process

**Quick template:**

```yaml
eval_id: category_descriptive_name_001
name: "Human-Readable Name"
description: "What this eval checks"
category: nextjs  # or react, supabase, etc.

# Optional runtime inputs
inputs:
  custom_variable: "default_value"

criteria: |
  You have access to the entire codebase. Evaluate [what to check].
  
  WHAT TO LOOK FOR:
  - [Specific patterns to search for]
  
  ANTI-PATTERN (mark as failed):
  - [Bad pattern 1]
  - [Bad pattern 2]
  
  CORRECT PATTERN (mark as passed):
  - [Good pattern 1]
  - [Good pattern 2]
  
  MARK AS N/A if:
  - [Condition for not applicable]
  
  Return JSON with: passed, score, summary, evidence, issues
```

## Use Cases

### 1. CI/CD Integration

Add to your CI pipeline to catch anti-patterns:

```yaml
# .github/workflows/evals.yml
name: Code Quality Evals
on: [push, pull_request]

jobs:
  evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run MicroEvals
        run: |
          pip install -r requirements.txt
          python -m microevals.eval_runner \
            --repo . \
            --category nextjs \
            --batch-size 10
```

### 2. Audit Existing Projects

Evaluate multiple repositories:

```bash
#!/bin/bash
repos=(
  "https://github.com/org/app1"
  "https://github.com/org/app2"
  "https://github.com/org/app3"
)

for repo in "${repos[@]}"; do
  echo "Evaluating $repo..."
  python -m microevals.eval_runner --repo "$repo" --all --batch-size 20
done
```

### 3. Pre-deployment Checks

Validate before deploying to production:

```bash
# Check production-critical patterns
python -m microevals.eval_runner \
  --repo https://github.com/org/production-app \
  --category vercel \
  --category supabase \
  --input deployment_url "https://app.vercel.app"
```

## Troubleshooting

### Claude CLI Not Found

```bash
# Ensure Claude CLI is installed and in PATH
which claude

# If not installed, see: https://docs.anthropic.com/en/docs/build-with-claude/cli
```

### Rate Limiting

If you hit Claude rate limits:

```bash
# Use batch mode to reduce API calls
python -m microevals.eval_runner --repo URL --all --batch-size 15

# Or add delays with single eval mode (automatic 2s delay)
python -m microevals.eval_runner --repo URL --all --parallel 1
```

### Timeout Issues

For large codebases, increase timeout:

```bash
python -m microevals.eval_runner \
  --repo URL \
  --all \
  --timeout 600 \
  --batch-size 10
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- How to submit new evals
- Testing requirements
- PR guidelines

**Quick contribution:**
1. Fork the repo
2. Create new eval in `evals/[category]/`
3. Test locally: `python -m microevals.eval_runner --eval your-eval.yaml --repo test-repo`
4. Submit PR

## License

MicroEvals operates under MIT license. Please see [LICENSE](LICENSE) for more details.

## Support

- [Issues](https://github.com/Design-Arena/MicroEvals/issues)
- Email: contact@designarena.ai

---

Built for better agent code quality. 
See more and try the evals live at [designarena.ai/evals](DesignArena.ai/evals).