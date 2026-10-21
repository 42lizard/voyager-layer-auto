# Voyager Layer Auto

Automatically select a Linux base layer when you plug in a ZSA Voyager.
Made for **Omarchy / Hyprland with Lua configuration**.

Keep your Mac layout on layer 0. On your Linux desktop, this user service
starts Keymapp when the Voyager appears, waits for its API, and selects your
Linux layer once. Manual layer changes afterwards are left alone.

Keymapp opens on a hidden `special:keymapp` workspace. Opening **Keymapp** from
the application launcher reveals its existing window instead of creating
another instance. A shared startup lock prevents the launcher and service
from starting duplicate instances at the same time.

## Requirements

- Linux, systemd user services, Python 3.9+, and `pgrep` (procps).
- Omarchy with Hyprland Lua configuration and its `o.window` helper.
  Tested on Hyprland 0.56.2; older `.conf` configurations are not supported.
- [Keymapp](https://www.zsa.io/flash), tested with 1.3.7.
- [Kontroll](https://github.com/zsa/kontroll) on your PATH or in `~/.local/bin`.
- A Voyager with firmware supporting the Keymapp API and working USB access.

The integration itself needs **no root privileges**. If Keymapp cannot access
your keyboard yet, the system's USB permissions may need separate setup using
[ZSA's Linux instructions](https://github.com/zsa/wally/wiki/Linux-install).

## Install

Open Keymapp, go to settings and start its **API**. Leave Keymapp's own login
autostart disabled: this service starts it only when a Voyager is connected.

```sh
git clone https://github.com/42lizard/voyager-layer-auto.git
cd voyager-layer-auto
./install --layer 3
```

Layer numbers start at zero. Choose your own Windows/Linux base layer;
`3` is just an example. The installer uses your user directory, installs the
scripts and service, adds a marked block to `hyprland.lua`, and overrides the
Keymapp launcher entry. Changed existing files receive a
`.before-voyager-layer-auto` backup. Re-running the installer updates files
without duplicating the marked configuration block.

`./install --layer 3 --no-start` writes files without contacting your desktop
session or enabling the service. To activate afterwards, reload Hyprland and run
`systemctl --user daemon-reload` followed by
`systemctl --user enable --now voyager-layer.service`.

## Use and configuration

Plug in your Voyager. Within a few seconds it should switch to your chosen
layer. A connected keyboard is also handled when you log in. The service
polls USB connection identity every half second, retries while the API starts,
and stops switching after one successful change per connection.

Open Keymapp through the application launcher or run:

```sh
~/.local/bin/keymapp-show
```

Use this command to toggle its workspace:

```sh
hyprctl eval 'hl.dispatch(hl.dsp.workspace.toggle_special("keymapp"))'
```

Settings live in `~/.config/voyager-layer/config.json` (or `$XDG_CONFIG_HOME`):

```json
{
  "layer": 3,
  "vendor": "3297",
  "product": "1977"
}
```

After editing, run `systemctl --user restart voyager-layer.service`.
This also switches the currently connected Voyager once.

## Troubleshooting

```sh
systemctl --user status voyager-layer.service
journalctl --user -u voyager-layer.service -f
kontroll status --json
hyprctl configerrors
```

If the service keeps waiting, open Keymapp settings and verify that the API is
running. Avoid starting `/usr/bin/keymapp` manually while another instance is
running; use the launcher or `keymapp-show` instead. Disable other tools that
automatically switch layers if they conflict with this service.

This requires an active graphical user session. The keyboard starts with its
firmware's default layer until the service has connected. It does not change
your firmware, Oryx layout, or persistent default layer. Support is intended
for a single Voyager; multiple Voyagers are not independently managed.

## Uninstall

```sh
./install --uninstall
```

This disables the service, removes the installed scripts, launcher override,
and marked Hyprland block, and restores backed-up destination files. The
layer configuration and Hyprland backup are retained. Keymapp, Kontroll, and
the API setting are left installed. Stopping the service also stops a Keymapp
instance it launched.

## Development

```sh
python3 -m unittest discover -s tests -v
```

The tests use temporary directories and mocked desktop/API commands. The
initial implementation was additionally tested with a real Voyager, Keymapp
1.3.7, and Hyprland 0.56.2 on Omarchy.

## License

[MIT](LICENSE). Unofficial project; not affiliated with ZSA.
