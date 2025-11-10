# Shadcn/UI Evaluation Suite Notes

## Current Status: ⭐⭐⭐⭐⭐ Excellent

The 7 shadcn evals are comprehensive and well-designed. They cover all critical setup issues.

## Possible Additions (Future)

### High Priority
1. **008_radix_ui_versions.yaml** - Check Radix UI version compatibility
   - Issue: Shadcn components break if Radix versions mismatch
   - Check: Verify @radix-ui packages are compatible versions

2. **009_lucide_icons.yaml** - Check lucide-react is installed
   - Issue: Most shadcn examples use lucide icons
   - Check: Verify lucide-react in package.json

### Medium Priority
3. **010_form_schema_validation.yaml** - Check Form component setup
   - Issue: Using Form without proper zod schema
   - Check: When Form component exists, verify zod schemas are used

4. **011_dark_mode_provider.yaml** - Check next-themes setup
   - Issue: Dark mode toggle without provider
   - Check: Verify next-themes and ThemeProvider wrapper

### Nice to Have
5. **012_component_imports.yaml** - Check import statements
   - Issue: Importing from wrong paths (node_modules instead of local)
   - Check: Verify imports are from @/components/ui, not shadcn directly

## Testing Priority

When testing, focus on these scenarios:
1. Fresh shadcn setup (should catch all missing configs)
2. Partial setup (some components added, config incomplete)
3. App Router vs Pages Router differences
4. TypeScript vs JavaScript projects

## Known Edge Cases

1. **Custom component paths**: Some projects use `src/components` vs `components`
   - Current evals handle this via path alias checking

2. **Manual installations**: Some devs copy-paste instead of using CLI
   - Evals should still catch missing dependencies

3. **Tailwind v4**: New @import syntax might affect CSS variable checks
   - May need to update 002_css_variables.yaml

## Integration Notes

These evals work best when:
- User prompt mentions "shadcn", "shadcn/ui", or specific components
- Codebase contains `components/ui/` directory
- components.json exists

Should return -1.0 (N/A) when:
- No shadcn components detected
- Using different UI library
- Plain React/Next.js without component library

