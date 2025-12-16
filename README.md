# LawCites to BePress Converter 📚

A Streamlit web app for converting exported Law Cites scholarship data into batch-upload-ready files for [Chicago Unbound](https://chicagounbound.uchicago.edu).  
**Developed by Gregory McCollum while at the D'Angelo Law Library, University of Chicago.**


---

## Overview

This app:

- Converts Law Cites reports into Chicago Unbound import templates (`ready.xls`) for books, book chapters, and articles.
- Compares Law Cites content against an CU inventory file to detect possible duplicates and generates a `review.csv` for manual review.
- Maps Law Cites data to corresponding Chicago Unbound fields.
- Tests links for incoming content, filtering out broken links and prioritizing DOIs where available
- Generates a complete, read-for-upload spreadsheet (`ready.xls`)
- Offers a ZIP folder containing both `ready.xls` and `review.csv` for download.


---

## How to Use

1. **Navigate to https://cwt3n8vj7a5rjntpfv9y6n.streamlit.app/**
    - You may need to select "Wake Up" to restart the app
2. **Upload Chicago Unbound Inventory**
    - Download the current inventory from Chicago Unbound [(Learn how)](https://digitalcommons.elsevier.com/reporting/content-reporting-tool). Save the inventory as a `.csv` file.
    - Upload under **"Upload Chicago Unbound inventory CSV file"**.
3. **Select Material Type**
    - Choose whether you are uploading Books, Book Chapters/Sections, or Articles.
4. **Upload LawCites Report**
    - Export your Law Cites report as a `.csv`.
    - Upload under **"Upload LawCites CSV file"**.
5. **Convert**
    - Click the **Convert** button.
    - Conversion will occur. Time will vary depending on the size of the document.
6. **Download Results**
    - Download the output ZIP file containing:
        - `ready.xls`: Entries ready for batch upload to corresponding Chicago Unbound series
        - `review.csv`: Entries that may duplicate existing inventory (manual review recommended).

--

## Mapping Description
For each of the entries in the submitted LawCites report the tool will
- Perform an initial mapping of the input data to the new format for values that can easily populate the new formatting in a one-to-one relationship (“title”, “custom_citation”, “publication_date”, “publisher”, “source_publication”).
- Extract editor values from the input “Author(s)” field and inserting them into the new “book_editors” field (if necessary)
- Identify each author name from the input “Author(s)” field and matching them with their corresponding “author{x}_fname” and “author{x}_lname” fields in the new data row.
- Evaludate the provided resouece links. For each link, the script will verify to perform an HTTP request to the designated URL and verify if a valid status code is received in the request, removing those that get a 404 error or some other form of invalid code. If multiple working links still exist and work, the script will select any like that adheres to the DOI format or points to an SSRN webpage as the primary one. If multiple valid links still remain, the first provided one will be selected
- Craft a catalog link with a catalog link if a bib number is provided.
- Add volume or issue number if provided.
- For items that lack any authors (as is required by the Digital Commons spreadsheet), utilize any provided editors as authors for that item. The editor(s) will still appear in the “editors” field.

---

## Notes
- If future edits are made to the metadata templates associated with the "articles", "books", and "book chapters" series on Chicago Unbound, changes will be necessary for this code to match those changes.
- This app is an adadptation of a tool I developed in 2024, which ran on my local machine. Information on that tool and its development is availble [here](https://drive.google.com/file/d/1pDHLZpi3ixwtgRb9yZZmuO5q3E8fnpJB/view?usp=sharing). Note that the pervious, local version of this tool notified the user of link conflicts in which there are not operational links or multiple operational links and prompted the user to provide one. This new, web-based verison performs its own link assessment and prioritization without prompting the user for input.


---

## Dependencies

- [Streamlit](https://streamlit.io/)
- [Requests](https://docs.python-requests.org/)
- [FuzzyWuzzy](https://github.com/seatgeek/fuzzywuzzy)
- [pyexcel](http://docs.pyexcel.org/en/latest/)

