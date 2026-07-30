# Ponytail Senior Developer Coding Principles

This project enforces **Ponytail Coding Standards** for high-performance, minimal-bloat, senior-developer quality code.

## Core Rules

1. **YAGNI (You Ain't Gonna Need It)**
   - Never write predictive abstractions, unused utility functions, or premature generalization.
   - Solve the current requirement with the simplest, most direct implementation.

2. **Decision Ladder**
   - **Level 1**: Use language built-ins and standard libraries first.
   - **Level 2**: Use existing project utilities before writing custom logic.
   - **Level 3**: Only introduce lightweight external packages when built-ins are genuinely insufficient.

3. **Zero-Bloat Code Architecture**
   - Keep functions small, focused, and single-purpose.
   - Prefer flat, readable code over deeply nested conditional logic or excessive design patterns.
   - Maintain zero unused imports and clean variable scopes.

4. **Transparent AI & Explicit Logic**
   - Avoid silent fallbacks, swallowed exceptions, or dummy return values.
   - Handle edge cases with explicit error handling and clear logging.
