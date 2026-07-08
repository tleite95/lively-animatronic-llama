---
name: ghs-codes
description: Provides information on the Globally Harmonized System of Classification and Labeling of Chemicals (GHS). Use as a reference to look up the meaning of specific GHS codes.
---

## Code identification
In GHS, hazard statements describe the nature and severity of the risks posed by a chemical, while precautionary statements provide actionable instructions on how to safely handle, store, and dispose of it to prevent accidents. To programmatically identify these codes, check strings against the following sequence of rules:
1. Identify H-Codes (Hazards)
    * Match criteria: Starts with a capital H, followed by exactly 3 digits, and ends with 0 to 2 letters (case-insensitive).
    * Regex pattern: `^H\d{3}[A-Za-z]{0,2}$`
    * Examples: H225, H360, H360Fd, H361d
2. Identify P-Codes (Precautions)
    * Match criteria: Starts with a capital P, followed by exactly 3 digits, and ends with 0 to 2 letters.
    * Regex pattern: `^P\d{3}[A-Za-z]{0,2}$`
    * Examples: P210, P302
3. Identify Combined Codes
    * Match criteria: Multiple valid H or P codes joined by a plus sign.
    * Regex pattern: `^(?:H\d{3}[A-Za-z]{0,2}\+H\d{3}[A-Za-z]{0,2}(?:\+H\d{3}[A-Za-z]{0,2})*|P\d{3}[A-Za-z]{0,2}\+P\d{3}[A-Za-z]{0,2}(?:\+P\d{3}[A-Za-z]{0,2})*)$`
    * Examples: H302+H312, P301+P310
4. Classification: "Neither"
    * Match criteria: Any string failing to match the previous rules.
    * Examples: EUH066, Precaution, H22, XYZ

## Data lookup
Then depending on what you matched:
* If you found neither, report that the code you were asked about is not part of the GHS system
* If you found a combined code, follow both of the following steps
* If You found H-Codes, find all corresponding entries in the table `./data/hazard-statements.xml` and search for relevant information. Then note all referenced P-Codes and read those.
* If You found P-Codes, find all corresponding entries in the list `./data/precautionary-statements.xml` and search for relevant information.

These files are html-style xml. You can parse them with the bs4 python library. Hazards are in a table, and you can find a particular row with the following snippet:

```python
target_row = soup.select_one('tr:has(td#<H-Code gere>)')
```

If that fails to return a result, try the following as a fallback:
```python
# 1. Find the td element by its id
target_td = soup.find('td', id='<H-Code here>')

# 2. Extract the parent tr tag
if target_td:
    target_row = target_td.find_parent('tr')
    print(target_row)
else:
    print("Element not found")
```

Precautions are just concatenated with each existing on a single line. To get the full line:

```python
# 1. Find the target tag by its text content
target_b = soup.find('b', string="P203:")

if target_b:
    # 2. Extract the bold text and its immediate trailing text sibling
    bold_text = target_b.get_text()
    trailing_text = target_b.next_sibling
    
    # 3. Combine them into a single string
    full_line = f"{bold_text} {trailing_text.strip()}"
    print(full_line)
```

Make sure you only look up one code at a time. If you are searching combined codes, you must tokenize them first and then search each individually.

## Reporting
Give a concise, well-formatted, markdown report of your findings. If specific questions were asked, answer them using the information from the data lookup. If you were not asked a specific question, summarize all findings as follows:

When reporting on hazards, list the signal word, hazard statement, and hazard class. Then give the precautionary statement texts verbatim for prevention, response, storage, and disposal. If multiple precautionary statements apply to a specific category, format them as an unordered list.

WHen reporting on precautions, return the statement text verbatim.