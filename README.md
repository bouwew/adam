# adam
Adam for Home Assistant Core (should also work on a Anna/Smile with firmware 3.x).

Configuration.yaml:

```
adam:
  password: the ID of the Adam (or Smile)
  host: the local IP address of the Adam (or Smile)
  scan_interval: 60 # (default = 30)
```

In combination with the Adam, Plugs are supported, including control.
NOTE: when there are more than one Plug, they will only be correctly detected when each Plug is configured with a unique Appliance name (Naam apparaat). Plugs can have the same Zone name (Naam zone).
