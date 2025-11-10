# Contributing Evaluations

Thank you for your interest in contributing to Agentic-Evals! We welcome contributions of new evaluation criteria to help identify common coding mistakes and anti-patterns.

## Quick Start

**Want to contribute an eval?** Here are two ways:

### Option 1: Submit via GitHub Issue (Easiest)
1. [Open a new issue](https://github.com/Design-Arena/Agentic-Evals/issues/new) with title: "New Eval: [Your Eval Name]"
2. Fill in the template below in the issue description
3. We'll create the eval and credit you!

### Option 2: Submit a Pull Request (Recommended)
1. Fork the repository
2. Create a new YAML file in the appropriate category folder
3. Test your eval locally (instructions below)
4. Submit a PR with your changes

---

## Eval Template

Copy this template to create a new eval:

```yaml
eval_id: category_descriptive_name_001
name: "Human-Readable Name"
description: "Brief description of what this eval checks"
category: nextjs  # or react, supabase, tailwind, typescript, vercel, shadcn

# Optional: Runtime inputs that can be overridden
inputs:
  custom_variable: "default_value"
  deployment_url: null  # null means required at runtime

criteria: |
  You have access to the entire codebase. Evaluate [specific pattern/issue].
  
  CONTEXT: This eval applies to [when it's relevant].
  
  WHAT TO LOOK FOR:
  Look for [specific files, patterns, or code structures].
  
  ANTI-PATTERN (mark as failed):
  - [Specific bad pattern 1]
  - [Specific bad pattern 2]
  - [Common mistake to catch]
  
  CORRECT PATTERN (mark as passed):
  - [Ideal implementation 1]
  - [Alternative correct approach 2]
  - [Best practice to follow]
  
  MARK AS N/A if:
  - [Condition that makes eval not applicable]
  - [Another condition for N/A]
  - [When feature doesn't exist in codebase]
  
  Write your results to: eval_result.json
  
  Return JSON:
  {
    "passed": true/false,
    "score": 1.0 | 0.0 | -1.0,
    "summary": "Brief explanation of what you found",
    "evidence": ["Specific file paths and line numbers"],
    "issues": ["Specific problems found or empty array"]
  }
```

### Scoring Guide
- **1.0 (PASS)**: All criteria met, no issues found
- **0.0 (FAIL)**: Anti-pattern detected or criteria not met
- **-1.0 (N/A)**: Pattern/feature not present in codebase

---

## Categories

Choose the most appropriate category:

- **`nextjs`** - Next.js App Router patterns, server/client components, routing
- **`react`** - React hooks, state management, component patterns
- **`supabase`** - Supabase auth, database, storage, RLS
- **`tailwind`** - Tailwind CSS configuration, utility classes
- **`typescript`** - TypeScript type safety, null checks, assertions
- **`vercel`** - Vercel deployment, configuration
- **`shadcn`** - shadcn/ui component library patterns

Not sure? Use `general` or suggest a new category in your PR/issue.

---

## Testing Your Eval Locally

### 1. Test Against a Single Repository

```bash
cd MicroEvals

# Test your eval
python -m microevals.eval_runner \
  --repo https://github.com/user/test-repo \
  --eval evals/your-category/your-eval.yaml

# Check the results
cat results/your_eval_id_*.json
```

### 2. Test With Runtime Inputs

```bash
python -m microevals.eval_runner \
  --repo https://github.com/user/test-repo \
  --eval evals/your-category/your-eval.yaml \
  --input deployment_url "https://myapp.vercel.app" \
  --input custom_var "test_value"
```

### 3. Test Against Multiple Repos

Create a test suite with repos that should pass/fail:

```bash
# Should PASS
python -m microevals.eval_runner --repo https://github.com/user/good-repo --eval evals/your-eval.yaml

# Should FAIL  
python -m microevals.eval_runner --repo https://github.com/user/bad-repo --eval evals/your-eval.yaml

# Should be N/A
python -m microevals.eval_runner --repo https://github.com/user/unrelated-repo --eval evals/your-eval.yaml
```

---

## Best Practices

### ✅ DO

1. **Be Specific**: Reference exact file patterns, line numbers, code snippets
   ```yaml
   evidence: ["src/app/page.tsx:15 - Missing 'use client' directive"]
   ```

2. **Provide Examples**: Show both good and bad code in criteria
   ```yaml
   ANTI-PATTERN:
   // ❌ Bad - async client component
   'use client'
   export default async function Page() { ... }
   
   CORRECT PATTERN:
   // ✅ Good - server component can be async
   export default async function Page() { ... }
   ```

3. **Clear N/A Logic**: Make it obvious when eval doesn't apply
   ```yaml
   MARK AS N/A if:
   - No app/ directory found (pages router project)
   - No server components detected
   ```

4. **Test Thoroughly**: Test against 3+ repos where it should pass, fail, and be N/A

5. **Use Variables**: Make evals configurable with runtime inputs
   ```yaml
   inputs:
     deployment_url: null  # Required at runtime
     min_components: "3"   # Default but overridable
   ```

### ❌ DON'T

1. **Don't be vague**: "Check if code is good" → "Check if components use proper error boundaries"

2. **Don't catch everything**: Focus on ONE specific pattern per eval

3. **Don't hardcode values**: Use `inputs` for URLs, keys, thresholds

4. **Don't skip testing**: Always test before submitting

5. **Don't duplicate**: Check existing evals first to avoid overlap

---

## Naming Conventions

### Eval ID Format
```
category_descriptive_name_nnn
```

Examples:
- `nextjs_server_component_001`
- `react_missing_useeffect_dependencies_001`
- `supabase_rls_policies_001`

### File Naming
```
category/nnn-descriptive-name.yaml
```

Examples:
- `nextjs/001-server-component.yaml`
- `react/001-missing-useeffect-dependencies.yaml`
- `supabase/011-security-rls-policies.yaml`

Use sequential numbers (001, 002, 003...) within each category.

---

## Submission Checklist

Before submitting your eval, make sure:

- [ ] Eval ID follows naming convention
- [ ] File is in correct category folder
- [ ] YAML is valid (test with `python -m yaml your-eval.yaml`)
- [ ] Tested against 3+ repos (pass/fail/n/a scenarios)
- [ ] Criteria is specific and actionable
- [ ] Evidence includes file paths and line numbers
- [ ] N/A conditions are clear
- [ ] No duplicate of existing eval
- [ ] Works with runtime inputs (if applicable)
- [ ] Includes usage example in PR description

---

## Example Submission (GitHub Issue)

```markdown
## New Eval: Next.js Missing Loading States

**Category**: nextjs

**Description**: Detects pages that fetch data but don't implement loading.tsx for streaming

**Anti-Pattern**: 
- Page.tsx has async data fetching
- No loading.tsx in same directory
- Poor UX due to long initial load

**Correct Pattern**:
- loading.tsx exists alongside page.tsx
- Uses Suspense boundaries
- Proper streaming setup

**Test Repos**:
- Pass: https://github.com/vercel/next.js/tree/canary/examples/app-dir-i18n-routing
- Fail: https://github.com/user/old-nextjs-app
- N/A: https://github.com/user/pages-router-app

**YAML** (attached below)
```

---

## Questions?

- 💬 [Open a discussion](https://github.com/Design-Arena/Agentic-Evals/discussions)
- 🐛 [Report an issue](https://github.com/Design-Arena/Agentic-Evals/issues)
- 📧 Email: contact@designarena.ai

Thank you for contributing! 🎉