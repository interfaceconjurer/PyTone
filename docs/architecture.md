# Architecture and engineering review

Reviewed 2026-11-15. Baseline: `71ea935` on `layout-borderless`.
Changes are isolated on `architecture-review` in a separate worktree.

## Assessment

The basic architecture fits a small, synchronous image conversion library and CLI.
Its useful separation is image processing, a plain color-data interchange format,
and independent output renderers. There is no need for a framework, plugin registry,
service layer, or class hierarchy to support the current behavior.

The original implementation had concrete data-integrity, compatibility, validation,
and rendering defects. This review corrects those defects and adds regression tests.
Passing tests substantiate the behaviors below; they cannot prove that every possible
image, environment, or future dependency version is free of defects.

## Module responsibilities

| Module | Responsibility |
| --- | --- |
| `core.py` | Decode and normalize images; resize, map glyphs, and compute colors. No printing or output-file writes. |
| `contracts.py` | Shared `RGB` and `ColorRows` aliases and validation for numeric values, glyphs, colors, and rectangular grids. |
| `color.py` | Terminal capability detection and ANSI rendering. |
| `html_output.py` | Escape and serialize self-contained HTML; optional save helper. |
| `svg_output.py` | Escape and serialize SVG; optional save helper. |
| `output.py` | Write complete UTF-8 output to a temporary sibling, then atomically replace the destination. |
| `cli.py` | Parse options, select one conversion/rendering path, enforce source-file protection, and report expected failures. |
| `__main__.py` | Guarded process entry point, shared with the installed console script. |

`ColorRows` remains a list of rows of `(character, (red, green, blue))` cells.
Renderers validate that grid, return strings, and do not modify their input. The
existing `image_to_ascii`, `get_color_data`, and renderer entry points are preserved.

## Findings and corrections

| Priority | Original finding | Correction and evidence |
| --- | --- | --- |
| High | Output could overwrite its source image, including through a filesystem alias. Direct file writes could truncate previous output before failing. | CLI rejects identical resolved paths, symlinks, and hard links, including default document filenames. Shared atomic output preserves existing content under simulated partial-write and replacement failures. Tests: `test_cli.py`, `test_output.py`. |
| High | `Pillow>=10.0` allowed versions without `get_flattened_data`, introduced in 12.1. On Pillow 10.0, even the baseline one-pixel conversion raised `AttributeError`. | Pixel extraction uses public grayscale bytes and RGB pixel access. The corrected conversion suite was also run successfully with Python 3.10 / Pillow 10.0 before the dependency security decision. |
| High | The dependency constraint permits Pillow releases with published decoder security advisories. | Require Pillow >=13.0 and Python >=3.11, as approved by Jordan; see below. |
| Medium | Zero widths, empty ramps, NaN/infinite adjustments, malformed images, and file failures could raise raw exceptions. Conflicting effects silently chose one branch. | Conversion and rendering boundaries reject invalid domains. CLI usage errors exit 2; expected conversion/file errors exit 1 on stderr. Rainbow and custom gradients are mutually exclusive. Tests include all output modes, corrupt/truncated files, oversized dimensions, and decompression-bomb rejection. |
| Medium | Source image lifetime depended on Pillow's lazy decoding and garbage collection. EXIF orientation and transparency were not normalized consistently, and palette images were resized before RGB conversion. | A context manager decodes the first frame, applies EXIF orientation, composites alpha over black, and detaches RGB data before closing the file. Tests cover success/failure closure, GIF, palette transparency, alpha, EXIF, and common modes. |
| Medium | Gradient coordinates never reached the last stop. The HSV conversion discarded each stop's brightness, turning a black gradient gray. | Normalize endpoints on non-singleton axes; use the first stop for a 1x1 image. One interpolation function handles two or more stops and preserves their brightness before shape modulation. Endpoint, single-axis, black-stop, and inversion regressions cover this behavior. |
| Medium | ANSI 256-color matching treated the color cube as evenly spaced and ignored the grayscale ramp. | Use the actual cube levels and compare the nearest cube and gray candidates by squared RGB distance. Tests cover exact cube colors and grayscale entries. |
| Medium | Renderers accepted malformed grids; HTML could divide by zero on an empty first row; empty SVG art returned an invalid empty document; SVG rendering changed ElementTree's global namespace registry. | Shared grid contracts, valid empty documents, escaped glyph/title tests, explicit rejection of invalid XML/UTF-8 text, and removal of the global namespace mutation. |
| Medium | Conversion options were repeated across three CLI branches. Broken pipes could print tracebacks or fail during interpreter shutdown. | One shared color conversion path and file writer; a process wrapper handles broken stdout pipes for both installed and module entry points. Subprocess tests execute outside the source checkout. |
| Medium | Automated verification covered 24 cases, without dedicated renderer, write-failure, packaging, or CI checks. Historical setup documents contradicted current requirements. | Expanded regression suite, explicit lint rules, formatting checks, pinned GitHub Actions with read-only permissions, source/wheel builds, wheel installation checks, and historical-document labels. |

## Dependency security policy

The original Python 3.10 requirement constrains the available Pillow releases.
Pillow 13.0.0 requires Python 3.11 or newer. The upstream
[Pillow 13 security notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html)
describe fixes absent from earlier releases, including native decoder issues.
[PyPI release metadata](https://pypi.org/pypi/Pillow/13.0.0/json) reports the Python
requirement and published advisory status. Advisory applicability depends on the
format, installed optional codecs, and operations; an advisory listing alone does
not establish that every issue is reachable through PeachPy.

Jordan approved raising the requirements to Python >=3.11 and Pillow >=13.0.
Package metadata, agent guidance, README requirements, lint target, and the CI
minimum-version job now agree. The runtime dependency remains Pillow alone.
At review time, PyPI lists no published advisories for Pillow 13.0.0; that is a
time-bound metadata check, not a guarantee against undiscovered vulnerabilities.

## Verification

The initial suite had 24 passing tests on Python 3.12.15 / Pillow 13.0.0, with one
Ruff failure for an unsorted `__all__`.

Before the security floor was raised, the corrected code also passed 206 tests on
Python 3.10.22 / Pillow 10.0.0. That historical check reproduced and verified the
compatibility repair; Python 3.10 is no longer supported by the package metadata.

The supported-version suite was run with warnings treated as errors on:

| Environment | Result |
| --- | --- |
| Python 3.11.15 / Pillow 13.0.0 | 208 passed. |
| Python 3.12.15 / Pillow 13.0.0 | 208 passed. |
| Python 3.15.0rc3 / Pillow 13.0.0 | 208 passed; preview interpreter. |
| Installed wheel, Python 3.12.15 / Pillow 13.0.0 | 208 passed outside the checkout. |

Source and wheel distributions build in isolated environments, including a wheel
built from the source distribution. Archive inspection confirms the wheel contains
only the package and distribution metadata, and the sdist contains the sources and
tests without scratch files or gallery assets. Ruff lint and formatting checks and
`git diff --check` pass.

CI covers supported Python versions, minimum dependency versions, macOS and
Windows, and distribution installation. The first Windows run exposed closed stdout
pipes reporting `OSError(EINVAL)` rather than `BrokenPipeError`. Stdout writes now
run outside conversion-error handling, and the process wrapper flushes argparse
output before shutdown as well. Regression tests cover art and `--help` output
through both entry points. See [PR #4](https://github.com/interfaceconjurer/ascii-image-generator/pull/4)
for current remote CI results.

## Intentional behavior and limits

- SVG's fixed 14px glyph size remains an intentional, documented density control;
  `--pixel-width` changes spacing. Short-ramp bucketing and the default glyph ramp
  are preserved to avoid gratuitously changing existing artwork.
- Applying EXIF orientation, alpha compositing, corrected gradients, and corrected
  ANSI matching can change newly generated output. Existing gallery assets were
  not regenerated, and browser typography was not visually compared across engines.
- A ramp entry is a Unicode code point. Grapheme clusters, emoji sequences,
  combining characters, and terminal column widths require font- and terminal-specific
  behavior beyond the current data model.
- The implementation decodes images and materializes output in memory. Pillow's
  image-size protections remain enabled, but callers can request large output.
  This is a local tool; deployment as an untrusted upload service would require
  explicit memory/CPU/output budgets and process isolation.
- Atomic replacement protects existing output from ordinary write/replace failures.
  It preserves existing permission bits and follows symlinks. It changes inode
  identity, does not preserve all filesystem metadata, and does not promise
  power-loss durability or coordination with concurrent external writers.
- No formal verification, decoder fuzzing campaign, universal visual comparison,
  or guarantee against future dependency vulnerabilities is implied by this review.
