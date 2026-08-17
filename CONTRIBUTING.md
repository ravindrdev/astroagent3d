# Contributing to AstroAgent 3D

Thank you for your interest in contributing! This guide covers the development workflow, architecture decisions, and how to get started.

## Getting started

```bash
# Clone the repo
git clone https://github.com/ravindrabhr/astroagent-3d.git
cd astroagent-3d

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests to verify setup
pytest tests/ -m "not slow" -v
```

## Development workflow

1. **Check existing issues** — look for `good-first-issue` labels
2. **Open an issue** describing what you want to work on
3. **Create a branch** from `main`: `git checkout -b feature/your-feature`
4. **Write code** with tests
5. **Run the full check suite:**
   ```bash
   ruff check src/ tests/
   ruff format src/ tests/
   pytest tests/ -m "not slow" -v
   mypy src/astroagent/
   ```
6. **Open a pull request** against `main`

## Pull request checklist

- [ ] Tests pass locally (`pytest tests/ -m "not slow"`)
- [ ] Linting passes (`ruff check src/ tests/`)
- [ ] New tools include Pydantic input schemas
- [ ] New tools include unit tests with mocked API calls
- [ ] Documentation updated if adding new features

## Adding a new tool

AstroAgent's tool system is designed for extensibility. To add a new astronomical data source:

1. Create `src/astroagent/tools/your_tool.py`
2. Subclass `AstroTool` and implement:
   - `name`: unique identifier (snake_case)
   - `description`: what Claude sees when deciding which tool to use
   - `input_schema`: Pydantic model with field descriptions
   - `execute()`: the actual implementation
3. Register it in `tools/__init__.py`
4. Add tests in `tests/test_tools/test_your_tool.py`

```python
from astroagent.tools.base import AstroTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    target: str = Field(description="Target name")

class MyTool(AstroTool):
    name = "my_tool"
    description = "What this tool does — Claude reads this to decide when to use it"
    input_schema = MyToolInput

    def execute(self, target: str) -> dict:
        # Your implementation here
        return {"result": "data"}
```

## Architecture Decision Records

### ADR-001: Claude over GPT-4 for the agent backbone

**Decision:** Use Anthropic's Claude API with native tool-use.

**Context:** Both Claude and GPT-4 support tool-calling for agentic workflows. We evaluated both for this scientific research use case.

**Rationale:**
- Claude's tool-use API provides structured, typed tool definitions via JSON Schema — a natural fit for Pydantic-based scientific tools
- Claude's extended thinking capability helps with multi-step reasoning about astronomical data
- The Anthropic SDK's message-based conversation model maps cleanly to our iterative query-refine workflow
- JupyterAI already ships with Claude support, aligning with our Jupyter integration goals

### ADR-002: Pydantic for tool input schemas

**Decision:** All tool inputs are defined as Pydantic BaseModel subclasses.

**Context:** Tool inputs need validation, documentation, and JSON Schema generation for Claude's tool-use API.

**Rationale:**
- Pydantic v2 generates JSON Schema natively via `model_json_schema()`, which is exactly what Claude's tool definition expects
- Field descriptions become part of the tool schema — Claude reads them to understand how to call each tool
- Runtime validation catches malformed inputs before they hit external APIs
- Type hints enable IDE autocompletion and mypy checking

### ADR-003: Three.js via CDN for 3D visualization

**Decision:** Load Three.js from CDN rather than bundling or requiring npm.

**Context:** The visualization needs to work inline in Jupyter notebooks without requiring users to install Node.js or run a build step.

**Rationale:**
- Jupyter renders HTML output directly — a self-contained HTML string with a CDN script tag "just works"
- No build toolchain dependency means `pip install` is the only setup step
- Three.js r128 is stable and widely cached on CDN
- The alternative (a JupyterLab extension with bundled JS) would require a separate `jupyter labextension install` step and TypeScript compilation

### ADR-004: Kopparapu et al. (2013) for habitable zone model

**Decision:** Use the Kopparapu et al. (2013) parameterization as the default habitable zone model.

**Context:** Multiple HZ models exist in the literature. We needed a well-cited, parameterized model that works across stellar types.

**Rationale:**
- Kopparapu+ 2013 is the most widely cited HZ model in exoplanet literature (2000+ citations)
- The polynomial parameterization by stellar effective temperature is computationally efficient
- It provides both conservative (runaway greenhouse → max greenhouse) and optimistic (recent Venus → early Mars) boundaries
- Coefficients are published in a well-known table, making the implementation verifiable

### ADR-005: Apache 2.0 license

**Decision:** License the project under Apache 2.0.

**Rationale:**
- Same license as Project Jupyter, NumPy, and most of the scientific Python ecosystem
- Permissive license allows academic and commercial use
- Patent clause provides additional legal clarity for contributors

## Code style

- Follow existing patterns in the codebase
- Use type hints everywhere (enforced by mypy strict mode)
- Ruff handles formatting and import sorting
- Keep tool implementations focused — one tool per data source

## Questions?

Open an issue with the `question` label and we'll help you get started.
