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
* If You found H-Codes, find all corresponding entries in `./data/hazard-statements.json` and search for relevant information. Then note all referenced P-Codes and read those.
* If You found P-Codes, find all corresponding entries in `./data/precautionary-statements.json` and search for relevant information.

### JSON structure overview

#### `hazard-statements.json`
An array of objects, one per hazard-code/category combination (the same H-code can appear multiple times if it applies to several categories). Each object has:
- `code` — the H-code (e.g. `"H290"`)
- `statement` — the hazard statement text
- `obsolete` — boolean
- `hazard_class`, `category` — classification fields
- `pictograms` — array of `{code, url}` objects
- `signal_word` — `"Danger"`, `"Warning"`, or `null`
- `un_class_or_division`, `un_placards` — transport classification (placards as `{code, title}`)
- `precautionary` — either `null`, or an object with four arrays: `prevention`, `response`, `storage`, `disposal`, each containing P-codes (some of which are combo codes joined with `+`)

#### `precautionary-statements.json`
A flat array of objects, one per P-code. Each object has:
- `code` — the P-code (including combo codes like `"P370+P380"`)
- `obsolete` — boolean
- `category` — which section it belongs to (General, Prevention, Response, Storage, Disposal)
- `text` — the instruction text

#### How they relate
The two files are linked by code: the P-codes listed in a hazard entry's `precautionary` block correspond to `code` values in the precautionary-statements file, letting you go from "what hazard" to "what to do about it."

### Notes on looking up data
- H-codes can have **multiple rows** (one per hazard category) — always loop over `h_index[code]`, don't assume a single match.
- P-code fields (`prevention`, `response`, `storage`, `disposal`) can contain **combo codes** like `"P370+P380"` — split on `"+"` before looking up in `p_index`.
  - Make sure you only look up one code at a time. If you are searching combined codes, you must tokenize them first and then search each individually!
- Missing data is `null` (scalars) or `[]` (lists) — check truthiness before indexing.
- Some statements are templates including ellipses. In these cases, note that the user must reference a specific SDS to fill it in.

## Reporting
Give a concise, well-formatted, markdown report of your findings. If specific questions were asked, answer them using the information from the data lookup. If you were not asked a specific question, summarize all findings as follows:

When reporting on hazards, list the signal word, hazard statement, and hazard class. Then give the precautionary statement texts verbatim for prevention, response, storage, and disposal. If multiple precautionary statements apply to a specific category, format them as an unordered list.

When reporting on precautions, return the statement text verbatim, as well as possibly a note on checking the SDS (as noted above).