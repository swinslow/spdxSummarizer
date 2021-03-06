# Additional features

## Importing SPDX files

A basic example of importing an SPDX tag-value file is described in [usage.md](usage.md).

### Importing unknown licenses

When creating a project scan database for the first time, you can pre-configure a set of categories of known licenses.

If you encounter unknown licenses when importing a scan's SPDX file, you will be prompted to create a license expression for it and to categorize it. You can also assign to existing categories or create a new category during import.

For example, suppose your `config.json` file did not include a `Copyleft` category at initialization. While importing a scan, if you encounter a file with an `AGPL-3.0` license, spdxSummarizer's importer will inform you that it does not recognize this license. It will prompt you to add the license to an existing category or to create a new category.

### License expression conversions

Before importing license expressions into spdxSummarizer, the SPDX parser automatically removes all "LicenseRef-" prefixes. This is intended to aid in readability of the generated reports by recipients who aren't familiar with the SPDX specification.

Additionally, some license expressions generated by automated tools may not be sufficiently informative for the intended audience of your reports. You can convert the license expression text to a different text by creating a conversion in one of two ways:

1. Set a conversion in the `config.json` file before creating the initial spdxSummarizer database for this project; or
2. Select the `Map to existing license` option when first encountering the license expression during scan import.

## Reporting options

### Excel summary report

The results of a scan can be exported into an Excel file, as described in the example in [usage.md](usage.md). This report will group together categories of licenses in separate tabs and will include a summary of all licenses in the first sheet.

### CSV file / license listing

The results of a scan can also be exported into a CSV file. This option will ignore categories, and will list each file with its corresponding license.

This may be a more useful format for project developers who plan to re-import the data into their own scripts.

### Excel comparison report of two scans

Additionally, the results of two scans can be compared and exported into an Excel file.

This option is intended for use with multiple scans of the same codebase over time (for example, comparing an initial scan against a re-scan of the same repository a month later).

The generated Excel report will have three sheets:
  * `Changed licenses`: files where the license information has changed between the first and second scan.
  * `In first only`: files that are found only in the first scan, and their corresponding licenses.
  * `In second only`: files that are found only in the second scan, and their corresponding licenses.

Note that the comparison is based solely on the filename. A file that is moved from one directory to another, but otherwise unchanged, will show up as `In first only` with its old path and `In second only` with its new path.

```
# SPDX-License-Identifier: CC-BY-4.0
```
