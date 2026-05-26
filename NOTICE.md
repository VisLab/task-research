# Third-party notices

This repository contains a slice of code vendored from another
open-source project.  The MIT licence under which that code is
distributed requires preservation of the copyright notice and the
licence text in any redistribution.  This file satisfies that
requirement.

---

## opencite

A small slice of code is vendored from the
[opencite](https://github.com/neuromechanist/opencite) project under
the terms of opencite's MIT licence.

**Pinned commit:** `3e784ddd067b75e73fd0c69e02e82142be1afe11`
(dated 2026-05-06).

**Vendored files** (in
`Claude-research/code/literature_search/vendored/opencite/`):

| File here | Upstream origin |
|---|---|
| `models.py` | `src/opencite/models.py` (slimmed to `IDType`, `IDSet`, `PDFLocation` only) |
| `url_parsers.py` | `parse_identifier` extracted from `src/opencite/models.py` |
| `pmc_convert.py` | `src/opencite/pmc_convert.py` (verbatim) |

**Not vendored** (mentioned for completeness):

- `src/opencite/clients/pmc.py` — opencite's PMC BioC client is
  async; we wrote a fresh sync version at
  `Claude-research/code/literature_search/clients/pmc.py` against
  the same documented endpoint.
- `src/opencite/convert.py` — opencite's PDF → Markdown wrapper
  uses markitdown / markit-mistral.  We use
  [marker-pdf](https://github.com/VikParuchuri/marker) for higher
  quality on academic papers; our thin wrapper lives at
  `Claude-research/code/literature_search/convert.py` as our own
  code, separate from this vendored slice.

See
`Claude-research/code/literature_search/vendored/opencite/README.md`
for the refresh policy and the rationale for vendoring rather than
depending on opencite as a package.

### opencite copyright notice and MIT licence (preserved verbatim)

```
MIT License

Copyright (c) 2026 Seyed Yahya Shirazi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
