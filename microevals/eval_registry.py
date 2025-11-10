"""
Eval Registry - Central catalog of all evaluations with applicability logic.

This module discovers all eval files and provides metadata about each eval,
including its category, dependencies, and applicability conditions.
"""

from pathlib import Path
from typing import List, Dict, Any
import yaml
import sys


class EvalRegistry:
    """Registry of all available evaluations."""
    
    def __init__(self, evals_dir: str = None):
        if evals_dir is None:
            # Try to find evals relative to package installation
            try:
                # Use importlib.resources for Python 3.9+ or fall back to __file__
                if sys.version_info >= (3, 9):
                    from importlib.resources import files
                    evals_dir = str(files('microevals').parent / 'evals')
                else:
                    # Fallback for older Python versions
                    evals_dir = str(Path(__file__).parent.parent / 'evals')
            except:
                # Final fallback - look relative to this file
                evals_dir = str(Path(__file__).parent.parent / 'evals')
        self.evals_dir = Path(evals_dir)
        self.evals = self._discover_evals()
    
    def _discover_evals(self) -> List[Dict[str, Any]]:
        """Discover all eval YAML files and load their metadata."""
        if not self.evals_dir.exists():
            raise ValueError(f"Evals directory '{self.evals_dir}' not found")
        
        evals = []
        yaml_files = sorted(list(self.evals_dir.rglob("*.yaml")) + list(self.evals_dir.rglob("*.yml")))
        
        for yaml_file in yaml_files:
            with open(yaml_file, 'r') as f:
                eval_data = yaml.safe_load(f)
                
            # Extract metadata
            eval_info = {
                "path": str(yaml_file),
                "relative_path": str(yaml_file.relative_to(self.evals_dir)),
                "eval_id": eval_data.get("eval_id", "unknown"),
                "name": eval_data.get("name", ""),
                "category": eval_data.get("category", "general"),
                "description": eval_data.get("description", ""),
                "inputs": eval_data.get("inputs", {}),
                
                # Applicability metadata
                "requires": self._extract_requirements(eval_data),
                "keywords": self._extract_keywords(eval_data),
            }
            
            evals.append(eval_info)
        
        return evals
    
    def _extract_requirements(self, eval_data: Dict[str, Any]) -> List[str]:
        """Extract technology/feature requirements from eval metadata."""
        requirements = []
        
        # Category-based requirements
        category = eval_data.get("category", "").lower()
        if category == "nextjs":
            requirements.append("nextjs")
        elif category == "supabase":
            requirements.append("supabase")
        elif category == "react":
            requirements.append("react")
        elif category == "tailwind":
            requirements.append("tailwind")
        elif category == "vercel":
            requirements.append("vercel")
        elif category == "shadcn":
            requirements.extend(["shadcn", "react", "tailwind"])
        
        # Explicit requirements from inputs
        inputs = eval_data.get("inputs", {})
        if "supabase_url" in inputs or "supabase_anon_key" in inputs:
            requirements.append("supabase")
        
        # Keyword-based requirements from eval_id and name
        eval_id = eval_data.get("eval_id", "").lower()
        name = eval_data.get("name", "").lower()
        
        if "server" in eval_id or "server" in name:
            requirements.append("server-component")
        if "client" in eval_id or "client" in name:
            requirements.append("client-component")
        if "action" in eval_id or "action" in name:
            requirements.append("server-action")
        if "cookie" in eval_id or "cookie" in name:
            requirements.append("cookies")
        if "auth" in eval_id or "auth" in name:
            requirements.append("authentication")
        if "zustand" in eval_id or "zustand" in name:
            requirements.append("zustand")
        if "metadata" in eval_id or "metadata" in name:
            requirements.append("metadata")
        if "route" in eval_id or "route" in name:
            requirements.append("routing")
        if "middleware" in eval_id or "middleware" in name:
            requirements.append("middleware")
        
        return list(set(requirements))
    
    def _extract_keywords(self, eval_data: Dict[str, Any]) -> List[str]:
        """Extract keywords from eval for matching."""
        keywords = []
        
        # From description and name
        description = eval_data.get("description", "").lower()
        name = eval_data.get("name", "").lower()
        
        # Handle criteria - it might be a string or list
        criteria = eval_data.get("criteria", "")
        if isinstance(criteria, str):
            criteria = criteria.lower()
        else:
            criteria = ""
        
        # Common keywords to extract
        all_text = f"{description} {name} {criteria}"
        
        keyword_list = [
            "fetch", "api", "database", "auth", "login", "signup",
            "cookie", "session", "server", "client", "component",
            "action", "form", "upload", "image", "file",
            "route", "router", "navigation", "link",
            "metadata", "seo", "og", "opengraph",
            "parallel", "intercepting", "loading", "error",
            "middleware", "revalidate", "cache", "streaming",
            "tailwind", "styling", "css", "ui", "shadcn",
            "supabase", "nextjs", "react", "vercel",
            "zustand", "state", "store", "hook"
        ]
        
        for keyword in keyword_list:
            if keyword in all_text:
                keywords.append(keyword)
        
        return list(set(keywords))
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all registered evals."""
        return self.evals
    
    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get evals by category."""
        return [e for e in self.evals if e["category"] == category]
    
    def get_by_id(self, eval_id: str) -> Dict[str, Any]:
        """Get eval by ID."""
        for e in self.evals:
            if e["eval_id"] == eval_id:
                return e
        raise ValueError(f"Eval with ID '{eval_id}' not found")
    
    def filter_by_requirements(self, requirements: List[str]) -> List[Dict[str, Any]]:
        """Filter evals that match any of the given requirements."""
        matching = []
        for e in self.evals:
            if any(req in e["requires"] for req in requirements):
                matching.append(e)
        return matching
    
    def print_summary(self):
        """Print a summary of all registered evals."""
        print(f"\n{'='*80}")
        print(f"EVAL REGISTRY SUMMARY")
        print(f"{'='*80}\n")
        print(f"Total evals: {len(self.evals)}\n")
        
        # Group by category
        categories = {}
        for e in self.evals:
            cat = e["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(e)
        
        for category, evals in sorted(categories.items()):
            print(f"{category.upper()} ({len(evals)} evals)")
            for e in evals:
                reqs = ", ".join(e["requires"]) if e["requires"] else "general"
                print(f"  - {e['eval_id']}: {e['name']}")
                print(f"    Requirements: {reqs}")
            print()


def main():
    """CLI for exploring the eval registry."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Explore the eval registry")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--list", action="store_true", help="List all evals")
    args = parser.parse_args()
    
    registry = EvalRegistry()
    
    if args.list:
        registry.print_summary()
    elif args.category:
        evals = registry.get_by_category(args.category)
        print(f"\nEvals in category '{args.category}':")
        for e in evals:
            print(f"  - {e['eval_id']}: {e['name']}")
    else:
        registry.print_summary()


if __name__ == "__main__":
    main()

