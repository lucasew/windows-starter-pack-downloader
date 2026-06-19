## IGNORE: Redundant Exception Handling

**- Pattern:** Wrapping all lower-level utility functions in try/except blocks to report errors.
**- Justification:** Causes duplicate error logging as exceptions bubble up. Centralized error reporting should handle try/except at the top-level execution (e.g., `main()`).
**- Files Affected:** `build.py`

## IGNORE: Out-of-Scope Code Formatting

**- Pattern:** Running full-file formatters (like `black`) alongside specific targeted fixes (e.g., adding docstrings).
**- Justification:** Introduces out-of-scope formatting changes to existing executable code, violating the mandate to isolate changes to specific tasks.
**- Files Affected:** `build.py`

## IGNORE: False Positive TLS Vulnerabilities

**- Pattern:** Adding explicit `ssl.create_default_context()` to `urllib.request.urlopen` calls.
**- Justification:** Python's `urlopen` validates TLS certificates by default. Adding an explicit default context is redundant.
**- Files Affected:** `build.py`

## IGNORE: Missing Mandatory Agent Journal Entries

**- Pattern:** Submitting PRs without creating or updating the required `.jules/janitor.md` or `.jules/sentinel.md` journal files.
**- Justification:** A journal entry is mandatory for every PR to keep a continuous record of automated changes.
**- Files Affected:** `.jules/janitor.md`, `.jules/sentinel.md`

## IGNORE: Redundant Zip Extraction Path Checks

**- Pattern:** Adding manual string checks for `..` or leading slashes in zip file members before extraction.
**- Justification:** `zipfile.ZipFile.extract()` safely handles and strips dangerous path components by default. Manual checks are unnecessary.
**- Files Affected:** `build.py`

## IGNORE: Manual Dependency Updates

**- Pattern:** Manually updating dependency versions in GitHub Actions workflows (e.g., bumping `actions/upload-artifact` to v5).
**- Justification:** The project uses Renovate (`renovate.json`) to automate dependency updates. Manual bumps cause conflicts.
**- Files Affected:** `.github/workflows/*.yml`

## IGNORE: False Positive SSRF / Local File Read in urlopen

**- Pattern:** Adding manual URL scheme validation (checking for `http://` or `https://`) before calling `urlopen`.
**- Justification:** Deemed a false positive or an overly restrictive check in the current execution context, rejected by reviewers.
**- Files Affected:** `build.py`
