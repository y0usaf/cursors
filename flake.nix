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

        capitalize = s: let
          first = builtins.substring 0 1 s;
          rest = builtins.substring 1 (-1) s;
        in (pkgs.lib.toUpper first) + rest;

        mkPopucomXcursor = color: pkgs.stdenv.mkDerivation {
          pname = "popucom-${color}-xcursor";
          version = "1.0.0";
          src = ./popucom/${color}/xcursor;
          sourceRoot = ".";
          installPhase = ''
            mkdir -p $out/share/icons/Popucom-${capitalize color}-x11
            cp -r $src/cursors $out/share/icons/Popucom-${capitalize color}-x11/
            cp $src/index.theme $out/share/icons/Popucom-${capitalize color}-x11/
          '';
          meta.description = "Popucom ${capitalize color} animated X11 cursor theme";
        };

        mkPopucomHyprcursor = color: pkgs.stdenv.mkDerivation {
          pname = "popucom-${color}-hyprcursor";
          version = "1.0.0";
          src = ./popucom/${color}/hyprcursor;
          sourceRoot = ".";
          dontFixTimestamps = true;
          installPhase = ''
            mkdir -p $out/share/icons/Popucom-${capitalize color}-hypr
            cp -r $src/hyprcursors $out/share/icons/Popucom-${capitalize color}-hypr/
            cp $src/manifest.hl $out/share/icons/Popucom-${capitalize color}-hypr/
          '';
          meta.description = "Popucom ${capitalize color} animated Hyprland cursor theme";
        };

        popucomColors = ["pink" "green" "blue" "yellow" "red" "orange" "cyan" "purple" "grey" "black" "inverted"];

        popucomPackages = builtins.listToAttrs (builtins.concatMap (color: [
          { name = "popucom-${color}-xcursor"; value = mkPopucomXcursor color; }
          { name = "popucom-${color}-hyprcursor"; value = mkPopucomHyprcursor color; }
        ]) popucomColors);
      in {
        packages = popucomPackages // {
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
