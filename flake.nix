{
  description = "Cursor Themes Collection (X11 and Hyprland)";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };
  outputs = {
    self,
    nixpkgs,
  }: let
    systems = ["x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin"];
    forAllSystems = nixpkgs.lib.genAttrs systems;
  in {
    packages = forAllSystems (system: let
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

      mkEarendilXcursor = variant: pkgs.stdenv.mkDerivation {
        pname = "earendil-${variant}-xcursor";
        version = "1.0.0";
        src = ./. + "/earendil-${variant}/xcursor";
        sourceRoot = ".";

        installPhase = ''
          runHook preInstall

          themeName="Earendil-${capitalize variant}-x11"
          outDir="$out/share/icons/$themeName"
          mkdir -p "$outDir"
          cp -r "$src/cursors" "$outDir/"
          cp "$src/index.theme" "$outDir/index.theme"

          runHook postInstall
        '';

        meta = {
          description = "Earendil ${capitalize variant} X11 cursor theme generated from the Earendil website SVG cursor";
          homepage = "https://earendil.com";
        };
      };

      mkEarendilHyprcursor = variant: pkgs.stdenv.mkDerivation {
        pname = "earendil-${variant}-hyprcursor";
        version = "1.0.0";
        src = ./. + "/earendil-${variant}/hyprcursor";
        sourceRoot = ".";
        dontFixTimestamps = true;

        installPhase = ''
          runHook preInstall

          themeName="Earendil-${capitalize variant}-hypr"
          outDir="$out/share/icons/$themeName"
          mkdir -p "$outDir"
          cp -r "$src/hyprcursors" "$outDir/"
          cp "$src/manifest.hl" "$outDir/manifest.hl"

          runHook postInstall
        '';

        meta = {
          description = "Earendil ${capitalize variant} Hyprland cursor theme generated from the Earendil website SVG cursor";
          homepage = "https://earendil.com";
        };
      };

      popucomColors = ["pink" "green" "blue" "yellow" "red" "orange" "cyan" "purple" "grey" "black" "inverted"];

      popucomPackages = builtins.listToAttrs (builtins.concatMap (color: [
        { name = "popucom-${color}-xcursor"; value = mkPopucomXcursor color; }
        { name = "popucom-${color}-hyprcursor"; value = mkPopucomHyprcursor color; }
      ]) popucomColors);
    in popucomPackages // {
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

      raccoin-xcursor = pkgs.stdenv.mkDerivation {
        pname = "raccoin-xcursor";
        version = "1.0.0";
        src = ./raccoin/xcursor;

        sourceRoot = ".";

        installPhase = ''
          mkdir -p $out/share/icons/Raccoin-x11
          cp -r $src/cursors $out/share/icons/Raccoin-x11/
          cp $src/index.theme $out/share/icons/Raccoin-x11/
        '';

        meta = {
          description = "Raccoin X11 cursor theme";
          homepage = "https://github.com/y0usaf/Cursors";
          license = pkgs.lib.licenses.mit;
        };
      };

      raccoin-hyprcursor = pkgs.stdenv.mkDerivation {
        pname = "raccoin-hyprcursor";
        version = "1.0.0";
        src = ./raccoin/hyprcursor;

        sourceRoot = ".";
        dontFixTimestamps = true;

        installPhase = ''
          mkdir -p $out/share/icons/Raccoin-hypr
          cp -r $src/hyprcursors $out/share/icons/Raccoin-hypr/
          cp $src/manifest.hl $out/share/icons/Raccoin-hypr/
        '';

        meta = {
          description = "Raccoin Hyprland cursor theme";
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

      earendil-dark-xcursor = mkEarendilXcursor "dark";
      earendil-light-xcursor = mkEarendilXcursor "light";
      earendil-dark-hyprcursor = mkEarendilHyprcursor "dark";
      earendil-light-hyprcursor = mkEarendilHyprcursor "light";
      default = self.packages.${system}.deepin-dark-xcursor;
    });
  };
}
