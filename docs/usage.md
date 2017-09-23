# Usage example

This is an example of how to use the basic importing and reporting functionality in spdxSummarizer.
We will import the SPDX tag-value file for spdxSummarizer itself, which is included in the distribution.

1. **Create a new spdxSummarizer database.**
  a. From the top-level spdxSummarizer directory, run: `./spdxSummarizer.sh ~/example.db`
  b. You will be prompted to create a new database. Enter `1`.
  c. You will be prompted to import a configuration file. We will use the default config file included with spdxSummarizer. Enter `spdxSummarizer/config.json`.

2. **Import the SPDX document.**
  a. You will be prompted to import an SPDX document from the initial scan. Enter `spdxSummarizer-2017-09-23.spdx`.
     (You may need to check the repository to see if the date/filename of the SPDX file has changed.)
  b. spdxSummarizer should successfully parse and identify all licenses in the file. Enter `1` to import the scan results into the database.
  c. At the following prompts, enter the date of the scan (`2017-09-23`) and a brief descripiton (e.g., `spdxSummarizer initial scan`).
  d. The scan should be successfully imported, and take you to the main menu.

3. **Generate an Excel summary report.**
  a. At the main menu, enter `3` to generate an Excel summary report.
  b. There should be exactly one scan listed in the database. Enter `1` to select it.
  c. Enter a filename with the location to save the Excel summary report (e.g., `spdxSummarizer-2017-09-23.xlsx`).
  d. You should see a notice that the Excel file listing was generated, and be taken back to the main menu.

4. **Open the Excel file and review the report.**
  a. Enter `X` to exit spdxSummarizer.
  b. Open the Excel file.
  c. The first sheet in the report, `License counts`, shows a summary of the file count for each license from the SPDX scan results.

Note the following details from the Excel report:
  * In this case, `Apache-2.0` and `CC-BY-4.0` are reported as `Project licenses` because they are the designated licenses for the spdxSummarizer project.
  * This is configurable in the `config.json` file that was used when the spdxSummarizer database was created, in step 1(c) above.
  * Files with no license information detected are labeled `No license found`.
  * Some files contain no license information, but are of a format where license info likely can't be easily added to the file itself (e.g., executables or image files). These files are labeled `No license found - excluded file extension`. The specific extensions that fall into this category are also configurable in the `config.json` file.
  * The other tabs, such as the `Project licenses` sheet, show a full listing of the files in that license category and the corresponding license for each file.

```
# SPDX-License-Identifier: CC-BY-4.0
```
