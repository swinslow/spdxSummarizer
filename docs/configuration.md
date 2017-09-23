# Configuration

Before creating an initial database for a project's scans, you can configure several parameters in a copy of the `config.json` file.

This is a standard JSON file format, with the following top-level keys:

### `"config"`:

At present, the main variable in the `"config"` section that is actually used by spdxSummarizer is `"ignore_extensions"`. This is a semicolon-separated list of filename extensions, intended to be files in which license expressions can't be easily inserted, such as image files or other binary data formats. As described in [usage.md](usage.md), these will be reported as `No license found - excluded file extension` if no license data was found.

Most other variables (such as project name, description, logo, etc.) are not currently used, but will likely be added to the spreadsheet report in a future version.

These values can be changed after the database is created by selecting option `1` (`Configure project database`) from the main menu.

### `"categories"`:

You can create and modify various categories of licenses to set up the groupings that are most useful for analyzing your project.

For example, because spdxSummarizer uses the [Apache 2.0 license](https://www.apache.org/licenses/LICENSE-2.0) for its source code and the [Creative Commons Attribution 4.0 International license](https://creativecommons.org/licenses/by/4.0/) for its documentation, the first category in the default `config.json` file (`Project licenses`) includes `Apache-2.0` and `CC-BY-4.0`. A project using different licenses would include different license expressions here.

The `No license found` category is expected by spdxSummarizer to be present, as part of its analysis and reporting of corresponding licenses.

Other categories can be removed or revised however you see fit.

We recommend including a category such as `Requires manual review` for licenses that you may wish to annotate or explain further in separate notes within the Excel report. This is not required by spdxSummarizer and can be omitted based on your workflow.

### `"conversions"`:

This allows configuration of initially-known license expression conversions. See the section on license expression conversions in [features.md](features.md) for more information.

```
# SPDX-License-Identifier: CC-BY-4.0
```
