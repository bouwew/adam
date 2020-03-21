# adam
Adam for Home Assistant Core (also works on a Anna/Smile with firmware 3.x).

Configuration.yaml:

```
adam:
  password: your ID
  host: the local IP address of the Adam (or Smile)
  scan_interval: 60 (default = 30)
```

With support for Plugs, including control.
NOTE: when there are more Plugs, they will only be correctly detected when each Plug is configured with a unique Appliance name (Naam apparaat).
