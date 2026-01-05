# Deepin Dark X11 Cursor Theme

An X11 cursor theme with a Deepin Dark style.

## Installation as a Flake

Add this flake to your `flake.nix` inputs:

```nix
inputs = {
  # ... other inputs
  deepin-dark-xcursor.url = "github:y0usaf/Deepin-Dark-xcursor";
};
```

Then, you can use the package in your Home Manager or NixOS configuration. For example, in Home Manager:

```nix
{ inputs, pkgs, ... }: {
  home.packages = [ inputs.deepin-dark-xcursor.packages.${pkgs.system}.default ];

  # Explicitly set as cursor theme
  home.pointerCursor = {
    name = "DeepinDarkV20-x11";
    package = inputs.deepin-dark-xcursor.packages.${pkgs.system}.default;
    size = 24; # Your preferred cursor size
    gtk.enable = true;
    x11.enable = true;
  };

  # For GTK applications
  gtk.cursorTheme = {
    name = "DeepinDarkV20-x11";
    package = inputs.deepin-dark-xcursor.packages.${pkgs.system}.default;
    size = 24; # Same as above
  };
}
```

## Manual Installation

1. Clone this repository.
2. Copy the `DeepinDarkV20-x11` directory (which will be in `result/share/icons/` after a `nix build .`) to `~/.local/share/icons/` or `/usr/share/icons/`.
3. Set the cursor theme in your desktop environment settings or configuration files.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.