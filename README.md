# Adam
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

## License, origins and contributors

Original (and therefor, license) by [haanna, anna-ha](https://github.com/laetificat) by Kevin Heruer

Modified and adjusted by @bouwew and @CoMPaTech in his repository.

# Thanks

On behalf of @CoMPaTech and @bouwew (as well as @riemers) we'd like to thank @TANE from [HAshop](https://hashop.nl) for his support and development devices
