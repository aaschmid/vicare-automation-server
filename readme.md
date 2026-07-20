# Settings

Can be either set via environment variable or `.env` file.
For more information how to get these values, see
[PyViCare](https://github.com/somm15/PyViCare#prerequisites).

* `CLIENT_ID`
* `EMAIL`
* `PASSWORD`

In addition, we added more value for further usecases.

To reach and check status of Apple TV:
* `APPLETV_HOST`
* `APPLETV_COMPANION_PORT`
* `APPLETV_COMPANION_IDENTIFIER`
* `APPLETV_COMPANION_CREDENTIALS`

# Pairing AppleTV

This is currently done manually with the following steps:

* Remove current config: `rm ~/.pyatv.conf`
* Start Pairing with `uv run atvremote wizard --protocol companion --remote-name "atvremote" --verbose`
* Look up identifier and credentials in `~/.pyatv.conf`
