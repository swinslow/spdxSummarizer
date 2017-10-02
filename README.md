# spdxSummarizer

## About

spdxSummarizer is a terminal-based set of tools for importing, analyzing and generating reports about files and licenses.

It imports [SPDX®](https://spdx.org/) tag-value files, and processes, categorizes and reports the license clearing results in various formats.

## Caveats

spdxSummarizer is _not_, itself, a license scanner. spdxSummarizer does not create SPDX files. It is only useful when used in conjunction with SPDX tag-value files that you've obtained from another source.

spdxSummarizer should be usable with arbitrary SPDX files. However, at present (2017-09-27) I have only tested it with SPDX tag-value files generated by [FOSSology](https://www.fossology.org/). I would gladly welcome feedback and patches from anyone who tries using spdxSummarizer with SPDX tag-value files generated using other tools.

## Workflow and usage

The intended workflow is:
1. obtain an SPDX tag-value file, such as by exporting it from a suitable license scanning tool;
2. import that tag-value file into spdxSummarizer; and
3. use spdxSummarizer to generate reports.

A walkthrough with a usage example, and further details about configuration and features, can be found in the file [`docs/usage.md`](docs/usage.md). Additional documentation is in other files in the `docs/` directory.

## Authors

The initial version of spdxSummarizer was written by Steve Winslow and is Copyright (C) 2017 The Linux Foundation.

## Requirements and dependencies

spdxSummarizer requires Python 3.6 or later.

spdxSummarizer uses the following dependencies, which should be installed using pip and are received under the following licenses:
- [XlsxWriter](https://github.com/jmcnamara/XlsxWriter) - [BSD-2-Clause-FreeBSD](https://github.com/jmcnamara/XlsxWriter/blob/master/LICENSE.txt)
- [SQLAlchemy](http://www.sqlalchemy.org/) - [MIT](https://github.com/zzzeek/sqlalchemy/blob/master/LICENSE)

As described above, spdxSummarizer is only useful in conjunction with SPDX files. SPDX is a registered trademark of The Linux Foundation.

## License

The spdxSummarizer source code is released under the [Apache 2.0 license](https://www.apache.org/licenses/LICENSE-2.0), a copy of which can be found in the file [`LICENSE-code.txt`](LICENSE-code.txt).

The spdxSummarizer documentation is released under the [Creative Commons Attribution 4.0 International license](https://creativecommons.org/licenses/by/4.0/), a copy of which can be found in the file [`LICENSE-docs.txt`](LICENSE-docs.txt).

This README.md file is documentation, and therefore gets the following:
```
SPDX-License-Identifier: CC-BY-4.0
```
