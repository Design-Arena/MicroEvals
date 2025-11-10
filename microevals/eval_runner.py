#!/usr/bin/env python
"""
Run Evaluations - Execute evaluations against a repository or local app.

Simplified eval runner that can:
1. Run a single eval
2. Run all evals in a category
3. Run all evals
4. Run specific eval IDs
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil

from .eval_registry import EvalRegistry
from .utils import prepare_repo, build_prompt, run_eval, run_batch_eval, load_source, read_result, save_results, safe_cleanup_temp_dir


# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def run_single_eval(eval_file: Path, repo_url: str, timeout: int = 300, output_dir: str = "results", runtime_inputs: dict = None) -> Dict[str, Any]:
    """Run a single evaluation against a repository."""
    # Handle both relative and absolute paths
    try:
        eval_name = str(eval_file.relative_to(Path("evals")))
    except ValueError:
        # If not relative to evals/, try to extract from absolute path
        parts = eval_file.parts
        if "evals" in parts:
            evals_index = parts.index("evals")
            eval_name = str(Path(*parts[evals_index+1:]))
        else:
            eval_name = eval_file.name
    
    try:
        # Load evaluation spec
        eval_spec = load_source("file", str(eval_file))
        
        # Merge runtime inputs with YAML defaults
        if runtime_inputs:
            yaml_inputs = eval_spec.get('inputs', {})
            merged_inputs = {**yaml_inputs, **runtime_inputs}
            eval_spec['inputs'] = merged_inputs
        
        # Prepare repository (clone or copy)
        temp_dir = prepare_repo(repo_url)
        
        try:
            # Build and run evaluation
            prompt = build_prompt(eval_spec)
            
            start_time = time.time()
            if not run_eval(temp_dir, prompt, timeout):
                return {
                    "eval_name": eval_name,
                    "eval_id": eval_spec.get("eval_id", "unknown"),
                    "status": "timeout",
                    "score": 0.0,
                    "duration": timeout,
                    "error": "Evaluation timed out"
                }
            
            duration = time.time() - start_time
            
            # Read results
            result = read_result(temp_dir)
            
            # Save results
            save_results(result, eval_spec, repo_url, output_dir)
            
            return {
                "eval_name": eval_name,
                "eval_id": eval_spec.get("eval_id", "unknown"),
                "status": "completed",
                "score": result.get("score", 0.0),
                "duration": duration,
                "summary": result.get("summary", "No summary provided")
            }
            
        finally:
            # Cleanup temp directory (with safety checks)
            safe_cleanup_temp_dir(temp_dir)
            
    except Exception as e:
        return {
            "eval_name": eval_name,
            "eval_id": "unknown",
            "status": "error",
            "score": 0.0,
            "duration": 0,
            "error": str(e)
        }


def print_result_line(result: Dict[str, Any]):
    """Print a single result line with color coding."""
    status = result["status"]
    score = result.get("score", 0.0)
    eval_name = result["eval_name"]
    
    # Determine status symbol and color
    if status == "error":
        symbol = "✗"
        color = Colors.RED
        status_text = "ERROR"
    elif status == "timeout":
        symbol = "⏱"
        color = Colors.YELLOW
        status_text = "TIMEOUT"
    elif score == 1.0:
        symbol = "✓"
        color = Colors.GREEN
        status_text = "PASS"
    elif score == -1.0:
        symbol = "○"
        color = Colors.BLUE
        status_text = "N/A"
    else:
        symbol = "✗"
        color = Colors.RED
        status_text = "FAIL"
    
    # Format duration
    duration = result.get("duration", 0)
    duration_str = f"{duration:.1f}s"
    
    print(f"{color}{symbol}{Colors.RESET} {status_text:8} {eval_name:50} {duration_str:>8}")
    
    # Print error or summary if available
    if result.get("error"):
        print(f"    {Colors.RED}Error: {result['error']}{Colors.RESET}")
    elif result.get("summary"):
        summary_text = result["summary"]
        if score == 1.0:
            print(f"    {Colors.GREEN}✓ {summary_text}{Colors.RESET}")
        elif score == -1.0:
            print(f"    {Colors.BLUE}○ {summary_text}{Colors.RESET}")
        else:
            print(f"    {Colors.RED}✗ {summary_text}{Colors.RESET}")


def print_summary(results: List[Dict[str, Any]]):
    """Print summary statistics."""
    total = len(results)
    passed = sum(1 for r in results if r.get("score") == 1.0)
    failed = sum(1 for r in results if r.get("score") == 0.0)
    na = sum(1 for r in results if r.get("score") == -1.0)
    errors = sum(1 for r in results if r.get("status") == "error")
    timeouts = sum(1 for r in results if r.get("status") == "timeout")
    
    total_duration = sum(r.get("duration", 0) for r in results)
    
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}SUMMARY{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"Total evaluations:  {total}")
    print(f"{Colors.GREEN}✓ Passed:          {passed}{Colors.RESET}")
    print(f"{Colors.RED}✗ Failed:          {failed}{Colors.RESET}")
    print(f"{Colors.BLUE}○ Not Applicable:  {na}{Colors.RESET}")
    print(f"{Colors.YELLOW}⏱ Timeouts:        {timeouts}{Colors.RESET}")
    print(f"{Colors.RED}✗ Errors:          {errors}{Colors.RESET}")
    print(f"Total duration:     {total_duration:.1f}s")
    
    # Calculate pass rate (excluding N/A)
    applicable = total - na
    if applicable > 0:
        pass_rate = (passed / applicable) * 100
        print(f"{Colors.BOLD}Pass rate:         {pass_rate:.1f}%{Colors.RESET} (excluding N/A)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Run evaluations against a repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in current directory
  microeval --category nextjs
  
  # Run in specific local path
  microeval --repo /path/to/project --category react
  
  # Run against remote repository
  microeval --repo https://github.com/user/app --eval evals/nextjs/001_server_component_fetch.yaml
  
  # Run a single eval with runtime input overrides
  microeval --repo https://github.com/user/app --eval evals/supabase/001_client_setup.yaml \\
    --input supabase_url "https://xyz.supabase.co" \\
    --input supabase_anon_key "your_key_here"
  
  # Run all evals in a category
  microeval --category nextjs
  
  # Run all evals in a category with runtime inputs (applies to all evals)
  microeval --category supabase --input deployment_url "https://myapp.vercel.app"
  
  # Run all evals
  microeval --all
  
  # Run specific eval IDs
  microeval --ids nextjs_server_component_fetch_001 supabase_implementation
  
  # Run with custom timeout and parallel execution
  microeval --category nextjs --timeout 600 --parallel 3
  
  # Run with batch mode (multiple evals in one Claude session)
  microeval --category tailwind --batch-size 3
  
  # Run all evals in large batches
  microeval --all --batch-size 15
  
  # Run specific eval files in batch
  microeval --evals evals/tailwind/001_tailwind_v4_config.yaml evals/react/001_missing_useeffect_dependencies.yaml --batch-size 2
        """
    )
    
    parser.add_argument('--repo', default='.', help='Repository URL or local path (default: current directory)')
    parser.add_argument('--eval', help='Path to specific evaluation YAML file')
    parser.add_argument('--evals', nargs='+', help='Paths to multiple evaluation YAML files')
    parser.add_argument('--category', help='Run all evals in this category (e.g., nextjs, supabase)')
    parser.add_argument('--ids', nargs='+', help='Run specific eval IDs')
    parser.add_argument('--all', action='store_true', help='Run all evaluations')
    parser.add_argument('--list', action='store_true', help='List all available evaluations and exit')
    parser.add_argument('--timeout', type=int, default=300, help='Evaluation timeout in seconds')
    parser.add_argument('--output-dir', default='results', help='Output directory for results')
    parser.add_argument('--parallel', type=int, default=1, help='Number of parallel evaluations')
    parser.add_argument('--evals-dir', default=None, help='Base directory containing evals (default: auto-detect from package installation)')
    parser.add_argument('--input', '-i', action='append', nargs=2, metavar=('KEY', 'VALUE'),
                        help='Runtime input override (can be used multiple times): --input key value')
    parser.add_argument('--batch-size', type=int, default=1,
                        help='Number of evals to run per Claude session (default: 1). Higher values are faster but less resilient.')
    parser.add_argument('--print-prompt', action='store_true',
                        help='Print the prompt before execution (useful for debugging batch mode)')
    
    args = parser.parse_args()
    
    # Initialize registry
    registry = EvalRegistry(args.evals_dir)
    
    # Handle --list option
    if args.list:
        print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}AVAILABLE EVALUATIONS{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")
        
        if args.category:
            # List specific category
            evals = registry.get_by_category(args.category)
            if not evals:
                print(f"{Colors.RED}No evals found in category '{args.category}'{Colors.RESET}")
                sys.exit(1)
            
            print(f"{Colors.CYAN}{args.category.upper()}{Colors.RESET} ({len(evals)} evals)\n")
            for eval_info in evals:
                print(f"  {Colors.GREEN}•{Colors.RESET} {eval_info['eval_id']}")
                print(f"    {eval_info['name']}")
                if eval_info.get('description'):
                    print(f"    {Colors.BLUE}{eval_info['description']}{Colors.RESET}")
                print()
        else:
            # List all categories
            all_evals = registry.get_all()
            print(f"Total evaluations: {Colors.BOLD}{len(all_evals)}{Colors.RESET}\n")
            
            # Group by category
            categories = {}
            for eval_info in all_evals:
                cat = eval_info['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(eval_info)
            
            for category, evals in sorted(categories.items()):
                print(f"{Colors.CYAN}{category.upper()}{Colors.RESET} ({len(evals)} evals)")
                for eval_info in evals[:3]:  # Show first 3
                    print(f"  {Colors.GREEN}•{Colors.RESET} {eval_info['eval_id']}: {eval_info['name']}")
                if len(evals) > 3:
                    print(f"  {Colors.YELLOW}  ... and {len(evals) - 3} more{Colors.RESET}")
                print()
            
            print(f"\n{Colors.CYAN}Tip:{Colors.RESET} Use --list --category <name> to see all evals in a category")
        
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")
        sys.exit(0)
    
    # Parse runtime inputs from --input arguments
    runtime_inputs = {}
    if args.input:
        for key, value in args.input:
            runtime_inputs[key] = value
        print(f"Runtime inputs: {runtime_inputs}\n")
    
    # Determine which evals to run
    eval_files = []
    
    if args.eval:
        # Single eval file
        eval_path = Path(args.eval)
        if not eval_path.exists():
            print(f"{Colors.RED}Error: Eval file '{args.eval}' not found{Colors.RESET}")
            sys.exit(1)
        eval_files = [eval_path]
        
    elif args.evals:
        # Multiple eval files
        eval_files = []
        for eval_file in args.evals:
            eval_path = Path(eval_file)
            if not eval_path.exists():
                print(f"{Colors.RED}Error: Eval file '{eval_file}' not found{Colors.RESET}")
                sys.exit(1)
            eval_files.append(eval_path)
        print(f"Running {len(eval_files)} specified evals")
        
    elif args.category:
        # All evals in category
        evals = registry.get_by_category(args.category)
        if not evals:
            print(f"{Colors.RED}Error: No evals found in category '{args.category}'{Colors.RESET}")
            sys.exit(1)
        eval_files = [Path(e["path"]) for e in evals]
        print(f"Running {len(eval_files)} evals in category '{args.category}'")
        
    elif args.ids:
        # Specific eval IDs
        for eval_id in args.ids:
            try:
                e = registry.get_by_id(eval_id)
                eval_files.append(Path(e["path"]))
            except ValueError:
                print(f"{Colors.YELLOW}Warning: Eval ID '{eval_id}' not found, skipping{Colors.RESET}")
        
        if not eval_files:
            print(f"{Colors.RED}Error: None of the specified eval IDs were found{Colors.RESET}")
            sys.exit(1)
            
    elif args.all:
        # All evals
        evals = registry.get_all()
        eval_files = [Path(e["path"]) for e in evals]
        print(f"Running all {len(eval_files)} evals")
        
    else:
        print(f"{Colors.RED}Error: Must specify --eval, --evals, --category, --ids, or --all{Colors.RESET}")
        sys.exit(1)
    
    # Run evaluations
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}Running evaluations for: {args.repo}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")
    
    results = []
    
    # Batch mode takes precedence over parallel mode
    if args.batch_size > 1 and len(eval_files) > 1:
        # Batch mode: run multiple evals in single Claude sessions
        print(f"{Colors.CYAN}Running in BATCH mode: {args.batch_size} evals per session{Colors.RESET}\n")
        
        # Load all eval specs
        eval_specs = []
        eval_names = []
        for eval_file in eval_files:
            try:
                eval_name = str(eval_file.relative_to(Path("evals")))
            except ValueError:
                parts = eval_file.parts
                if "evals" in parts:
                    evals_index = parts.index("evals")
                    eval_name = str(Path(*parts[evals_index+1:]))
                else:
                    eval_name = eval_file.name
            
            spec = load_source("file", str(eval_file))
            if runtime_inputs:
                spec['inputs'] = {**spec.get('inputs', {}), **runtime_inputs}
            eval_specs.append(spec)
            eval_names.append(eval_name)
        
        # Prepare repo once (clone or copy)
        print(f"{Colors.CYAN}Preparing repository...{Colors.RESET}")
        temp_dir = prepare_repo(args.repo)
        
        try:
            # Process evals in batches
            for i in range(0, len(eval_specs), args.batch_size):
                batch = eval_specs[i:i+args.batch_size]
                batch_names = eval_names[i:i+args.batch_size]
                batch_num = (i // args.batch_size) + 1
                total_batches = (len(eval_specs) + args.batch_size - 1) // args.batch_size
                
                print(f"{Colors.CYAN}[Batch {batch_num}/{total_batches}]{Colors.RESET} Running {len(batch)} evals...")
                
                # Print prompt if requested
                if args.print_prompt:
                    from .utils import build_prompt
                    import yaml
                    
                    # Build the batch prompt for display
                    batch_criteria = []
                    for i, spec in enumerate(batch, 1):
                        eval_id = spec['eval_id']
                        criteria = spec['criteria']
                        inputs = spec.get('inputs', {})
                        if inputs:
                            for key, value in inputs.items():
                                if value is not None:
                                    criteria = criteria.replace(f"{{{key}}}", str(value))
                        batch_criteria.append(f"""
{'='*80}
EVALUATION {i}/{len(batch)}
{'='*80}
EVAL ID: {eval_id}
FILENAME: eval_result_{eval_id}.json

CRITERIA:
{criteria}
""")
                    
                    # Load template
                    from pathlib import Path as P
                    judge_prompt_path = P(__file__).parent.parent / 'config' / 'judge_system_prompt.yaml'
                    with open(judge_prompt_path, 'r') as f:
                        prompts = yaml.safe_load(f)
                        template = prompts['batch_judge_prompt']['instruction_template']
                    
                    prompt = template.format(
                        eval_count=len(batch),
                        batch_criteria='\n'.join(batch_criteria)
                    )
                    
                    print(f"\n{Colors.YELLOW}{'='*80}{Colors.RESET}")
                    print(f"{Colors.YELLOW}BATCH PROMPT (for review):{Colors.RESET}")
                    print(f"{Colors.YELLOW}{'='*80}{Colors.RESET}")
                    print(prompt)
                    print(f"{Colors.YELLOW}{'='*80}{Colors.RESET}\n")
                    
                    # Ask for confirmation
                    response = input(f"{Colors.CYAN}Press Enter to continue or Ctrl+C to cancel...{Colors.RESET}")
                
                start_time = time.time()
                batch_results = run_batch_eval(temp_dir, batch, timeout=args.timeout)
                duration = time.time() - start_time
                
                # Process results for this batch
                for spec, eval_name in zip(batch, batch_names):
                    eval_id = spec['eval_id']
                    
                    if eval_id in batch_results:
                        result = batch_results[eval_id]
                        
                        # Save results if successful
                        if result.get('status') != 'error':
                            save_results(result, spec, args.repo, args.output_dir)
                        
                        # Add to results list
                        result_entry = {
                            "eval_name": eval_name,
                            "eval_id": eval_id,
                            "status": result.get("status", "completed"),
                            "score": result.get("score", 0.0),
                            "duration": duration / len(batch),  # Approximate per-eval duration
                            "summary": result.get("summary", result.get("error", ""))
                        }
                        if result.get("error"):
                            result_entry["error"] = result["error"]
                        
                        results.append(result_entry)
                        print_result_line(result_entry)
                    else:
                        # Eval not in results (shouldn't happen, but handle it)
                        result_entry = {
                            "eval_name": eval_name,
                            "eval_id": eval_id,
                            "status": "error",
                            "score": 0.0,
                            "duration": 0,
                            "error": "Result not found in batch output"
                        }
                        results.append(result_entry)
                        print_result_line(result_entry)
                
                print()  # Blank line between batches
        
        finally:
            # Cleanup temp directory (with safety checks)
            print(f"{Colors.CYAN}Cleaning up...{Colors.RESET}")
            safe_cleanup_temp_dir(temp_dir)
    
    elif args.parallel > 1:
        # Run evaluations in parallel
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = {
                executor.submit(run_single_eval, eval_file, args.repo, args.timeout, args.output_dir, runtime_inputs): eval_file
                for eval_file in eval_files
            }
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                print_result_line(result)
    else:
        # Run evaluations sequentially
        for i, eval_file in enumerate(eval_files, 1):
            print(f"{Colors.CYAN}[{i}/{len(eval_files)}]{Colors.RESET} Running {eval_file.name}...")
            result = run_single_eval(eval_file, args.repo, args.timeout, args.output_dir, runtime_inputs)
            results.append(result)
            print_result_line(result)
    
    # Print summary
    print_summary(results)
    
    print(f"{Colors.BOLD}{Colors.GREEN}All evaluations complete!{Colors.RESET}\n")


if __name__ == "__main__":
    main()

