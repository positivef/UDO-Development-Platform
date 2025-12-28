# Repository Guidelines

## Project Structure & Module Organization
Core logic lives in `src/`, where `unified_development_orchestrator_v2.py` drives phase orchestration, `uncertainty_map_v3.py` models predictive risk, and `three_ai_collaboration_bridge.py` coordinates agents.
Scenario runners (`tests/run_udo_phase1.py`) and pytest suites (`tests/test_udo_v3_integration.py`) live under `tests/` alongside new regression assets.
Analytical notes belong to `docs/`, while learned artifacts such as `data/udo_learning_data.json` and `data/udo_state_phase1.json` stay isolated in `data/`.
Mirror this layout when you add modules or datasets, and keep generated assets outside `src/` and `tests/`.

## Build, Test, and Development Commands
- `python -m venv .venv && .\.venv\Scripts\activate` -- create and activate the repository virtual environment on Windows shells.
- `pip install -r requirements.txt` -- install runtime and tooling dependencies.
- `python src\unified_development_orchestrator_v2.py` -- run the orchestrator demo to validate end-to-end wiring.
- `pytest tests` or `pytest --maxfail=1 --disable-warnings -q` -- execute the automated suite; use the strict flag set before a pull request.
- `python tests\run_udo_phase1.py` -- replay the phase drill scenario for targeted debugging.
- `black src tests` and `flake8 src tests` -- enforce formatting and linting prior to review.

## Coding Style & Naming Conventions
Write Python 3.11+ with four-space indentation, type hints on public APIs, and concise docstrings.
Use PascalCase for classes and dataclasses (`UnifiedDevelopmentOrchestratorV2`), snake_case for modules, and SCREAMING_SNAKE_CASE for constants.
Favor `@dataclass` payloads and explicit enums over loosely typed dicts, and guard Windows specific encoding logic similar to the orchestrator module.

## Testing Guidelines
Place new tests beneath `tests/` using the `test_*.py` pattern and realistic multi-phase fixtures.
Persist any synthetic state in `data/` rather than embedding JSON blobs in code or tests.
Always run `pytest` plus any scenario scripts touched by the change, and capture CLI output when triaging regressions.

## Commit & Pull Request Guidelines
Follow the sentence style prefix `<scope>: <concise outcome>` (example: `uncertainty: tighten learning rate`).
Keep commits focused; cross cutting work belongs in separate commits backed by clear explanations.
Pull requests must describe motivation, summarize the solution, link related issues, and attach logs or screenshots such as pytest output or `run_udo_phase1.py` transcripts.
Flag schema, data, or docs updates explicitly so reviewers can verify downstream consumers.

## Security & Configuration Tips
Never commit real credentials or proprietary datasets; the JSON files in `data/` are placeholders only.
Store secrets in a local `.env` that remains untracked, and scrub logs before sharing them with other agents.
Review generated plans and artifacts before committing, especially when they include sanitized client context.
