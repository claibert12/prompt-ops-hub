# demo-repo

A project with integrity gates enforced.

## Features

- **Coverage Gates**: Minimum 80% global coverage, 100% diff coverage
- **Test Quality**: No trivial tests, no skipped tests
- **Tamper Protection**: Test/config changes require #TEST_CHANGE markers
- **Policy Enforcement**: Configurable integrity policies
- **Observer Pattern**: Comprehensive logging of all checks

## Quick Start

1. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Run integrity checks:
   ```bash
   # Coverage check
   python -c "from integrity_core import CoverageChecker; CoverageChecker().check()"
   
   # Diff coverage check
   python -c "from integrity_core import DiffCoverageChecker; DiffCoverageChecker().check()"
   
   # Trivial test check
   python -c "from integrity_core import TrivialTestChecker; TrivialTestChecker().check()"
   
   # Tamper check
   python -c "from integrity_core import TamperChecker; TamperChecker().check()"
   ```

4. Run mutation tests:
   ```bash
   python scripts/run_mutation_tests.py
   ```

## Integrity Gates

### Coverage Requirements
- Global coverage must be >=80%
- Diff coverage must be 100% on changed lines
- Coverage thresholds cannot be lowered

### Test Requirements
- No skipped or xfail tests
- No trivial tests (unless marked with #ALLOW_TRIVIAL)
- All new code must have tests

### Change Requirements
- Test/config changes require #TEST_CHANGE marker
- Policy violations must be addressed
- Observer logs all integrity events

## Configuration

Edit `config/guardrails.conf` to customize integrity gate settings.

### Environment Variables

- `JWT_SECRET` – Secret key for verifying JSON Web Tokens used in API authentication.
- `JWT_ALGORITHM` – (Optional) JWT signing algorithm, default is `HS256`.
- `ALLOWED_ORIGINS` – Comma-separated list of origins allowed by the CORS middleware.
- `LOG_LEVEL` – Application log level (e.g., `INFO`, `DEBUG`).
- `SENTRY_DSN` – (Optional) DSN for sending error telemetry to Sentry.
- `GITHUB_TOKEN` – Token used by the GitHub adapter for creating branches and pull requests.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all integrity gates pass
6. Submit a pull request

## License

MIT License
