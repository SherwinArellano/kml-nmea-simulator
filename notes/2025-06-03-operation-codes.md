# Operation Codes Generation

_June 3, 2025_

**Objective:** To generate the following codes:
- `code_trailer`
- `code_container`
- `destination-port`
- `cod_prov`
- `cod_comune`

## `code_trailer`

It will be **randomly generated** based on the syntax: 2 letters - 3 numbers - 2 letters, e.g. TA487PZ.

## `code_container`

It will be **randomly generated** based on the syntax: 3 letters - 4 numbers, e.g. BSE1212.

## `destination-port`

It's a fixed value with format 1 letter and 2 numbers, e.g. A01.

I don't know if the format is actually like that and I have no idea why this value is fixed. Probably because this is just to mock the real operation payload.

Perhaps I can make it settable by creating a new KML option to specify `destination-port`. **If not set, then just use `A01`.** (To be clarified with the team.)

## `cod_prov`

There exists a `.json` file which has a list of code-province pair.

Create a map of this json file.

Generation logic:
1. Check if `<name>` in KML contains province in the json file. If so, use it.
2. If no province found in `<name>`, check if a `prov` option is provided and use it. (`prov` can be either a code or the name of the province)
3. If none found, console log that no province found for the track.

## `cod_comune`

There exists a `.json` file which has a list of code-province pair.

Create a map of this json file.

Generation logic:
1. Check if `<name>` in KML contains comune (municipality) in the json file. If so, use it.
2. If no comune found in `<name>`, check if a `comune` option is provided and use it. (`comune` can be either a code or the name of the municipality)
3. If none found, console log that no municipality found for the track.
