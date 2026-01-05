{
  description = "Cursor Themes Collection (X11 and Hyprland)";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {inherit system;};
      in {
        packages = {
          deepin-dark-xcursor = pkgs.stdenv.mkDerivation {
            pname = "deepin-dark-xcursor";
            version = "1.0.0";
            src = ./deepin-dark/xcursor;

            sourceRoot = ".";

            installPhase = ''
                            mkdir -p $out/share/icons/DeepinDarkV20-x11
                            if [ -d "$src/cursors" ]; then
                              cp -r $src/cursors $out/share/icons/DeepinDarkV20-x11/
                            fi
                            if [ -f "$src/index.theme" ]; then
                              cp $src/index.theme $out/share/icons/DeepinDarkV20-x11/
                            else
                              cat > $out/share/icons/DeepinDarkV20-x11/index.theme << EOF
              [Icon Theme]
              Name=DeepinDarkV20-x11
              Comment=Deepin Dark X11 Cursor Theme
              EOF
                            fi
            '';

            meta = {
              description = "Deepin Dark X11 cursor theme";
              homepage = "https://github.com/y0usaf/Cursors";
              license = pkgs.lib.licenses.mit;
            };
          };

          deepin-dark-hyprcursor = pkgs.stdenv.mkDerivation {
            pname = "deepin-dark-hyprcursor";
            version = "1.0.0";
            src = ./deepin-dark/hyprcursor;

            sourceRoot = ".";
            dontFixTimestamps = true;

            installPhase = ''
              mkdir -p $out/share/icons/DeepinDarkV20-hypr
              if [ -d "$src/hyprcursors" ]; then
                cp -r $src/hyprcursors $out/share/icons/DeepinDarkV20-hypr/
              fi
              if [ -f "$src/manifest.hl" ]; then
                cp $src/manifest.hl $out/share/icons/DeepinDarkV20-hypr/
              else
                printf '%s\n' 'name = DeepinDarkV20-hypr' \
                  'description = Deepin Dark Cursor Theme for Hyprland' \
                  'version = 1.0' \
                  'cursors_directory = hyprcursors' > $out/share/icons/DeepinDarkV20-hypr/manifest.hl
              fi
            '';

            meta = {
              description = "Deepin Dark Hyprland cursor theme";
              homepage = "https://github.com/y0usaf/Cursors";
              license = pkgs.lib.licenses.mit;
            };
          };

          ssb-xcursor = pkgs.stdenv.mkDerivation {
            pname = "ssb-xcursor";
            version = "1.0.0";
            src = ./ssb/xcursor;

            sourceRoot = ".";

            installPhase = ''
              mkdir -p $out/share/icons/SSB-x11
              if [ -d "$src/cursors" ]; then
                cp -r $src/cursors $out/share/icons/SSB-x11/
              fi
              if [ -f "$src/index.theme" ]; then
                cp $src/index.theme $out/share/icons/SSB-x11/
              else
                cat > $out/share/icons/SSB-x11/index.theme << EOF
              [Icon Theme]
              Name=SSB-x11
              Comment=Super Smash Bros Ultimate X11 Cursor Theme
              EOF
              fi
            '';

            meta = {
              description = "Super Smash Bros Ultimate X11 cursor theme";
              homepage = "https://github.com/y0usaf/Cursors";
              license = pkgs.lib.licenses.mit;
            };
          };

          default = self.packages.${system}.deepin-dark-xcursor;
        };
      }
    );
}
