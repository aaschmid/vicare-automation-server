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
* `APPLETV_COMPANION_IDENTIFIER`
* `APPLETV_COMPANION_CREDENTIALS`

# Pairing AppleTV

This is currently done manually with the following steps:

* Remove current config: `rm ~/.pyatv.conf`
* Start Pairing with `uv run atvremote wizard --protocol companion --remote-name "atvremote" --verbose`
* Look up identifier and credentials in `~/.pyatv.conf`

# AppleTV status endpoint

`GET /appletv` returns the current AppleTV system status:

```json
{
  "active": 1,
  "atv": {"host": "192.168.1.100", "port": 49153, "status": "connected"},
  "idle": 0,
  "state": "awake",
  "screensaver": 0
}
```

`state` is one of `awake`, `screensaver`, `idle`, `asleep`, `unknown`. `active` is `1` unless
the state is `asleep` or `unknown`. `idle` and `screensaver` are `1` when the state matches.
The connection is re-established transparently on connection loss; if the device is
unreachable the endpoint responds with `503`.
