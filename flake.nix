{
  description = "Cursor Themes Collection (Xcursor and Hyprland)";
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
          mkdir -p $out/share/icons/Popucom-${capitalize color}-xcursor
          cp -r $src/cursors $out/share/icons/Popucom-${capitalize color}-xcursor/
          cp $src/index.theme $out/share/icons/Popucom-${capitalize color}-xcursor/
        '';
        meta.description = "Popucom ${capitalize color} animated Xcursor theme";
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

          themeName="Earendil-${capitalize variant}-xcursor"
          outDir="$out/share/icons/$themeName"
          mkdir -p "$outDir"
          cp -r "$src/cursors" "$outDir/"
          cp "$src/index.theme" "$outDir/index.theme"

          runHook postInstall
        '';

        meta = {
          description = "Earendil ${capitalize variant} Xcursor theme generated from the Earendil website SVG cursor";
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
          mkdir -p $out/share/icons/Deepin-Dark-xcursor
          if [ -d "$src/cursors" ]; then
            cp -r $src/cursors $out/share/icons/Deepin-Dark-xcursor/
          fi
          if [ -f "$src/index.theme" ]; then
            cp $src/index.theme $out/share/icons/Deepin-Dark-xcursor/
          else
            cat > $out/share/icons/Deepin-Dark-xcursor/index.theme << EOF
          [Icon Theme]
          Name=Deepin-Dark-xcursor
          Comment=Deepin Dark Xcursor Theme
          EOF
          fi
        '';

        meta = {
          description = "Deepin Dark Xcursor theme";
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
          mkdir -p $out/share/icons/Deepin-Dark-hyprcursor
          if [ -d "$src/hyprcursors" ]; then
            cp -r $src/hyprcursors $out/share/icons/Deepin-Dark-hyprcursor/
          fi
          if [ -f "$src/manifest.hl" ]; then
            cp $src/manifest.hl $out/share/icons/Deepin-Dark-hyprcursor/
          else
            printf '%s\n' 'name = Deepin-Dark-hyprcursor' \
              'description = Deepin Dark Cursor Theme for Hyprland' \
              'version = 1.0' \
              'cursors_directory = hyprcursors' > $out/share/icons/Deepin-Dark-hyprcursor/manifest.hl
          fi
        '';

        meta = {
          description = "Deepin Dark Hyprland cursor theme";
          homepage = "https://github.com/y0usaf/Cursors";
          license = pkgs.lib.licenses.mit;
        };
      };

      deepin-light-xcursor = pkgs.stdenv.mkDerivation {
        pname = "deepin-light-xcursor";
        version = "1.0.0";
        src = ./deepin-light/xcursor;

        sourceRoot = ".";

        installPhase = ''
          mkdir -p $out/share/icons/Deepin-Light-xcursor
          if [ -d "$src/cursors" ]; then
            cp -r $src/cursors $out/share/icons/Deepin-Light-xcursor/
          fi
          if [ -f "$src/index.theme" ]; then
            cp $src/index.theme $out/share/icons/Deepin-Light-xcursor/
          else
            cat > $out/share/icons/Deepin-Light-xcursor/index.theme << EOF
          [Icon Theme]
          Name=Deepin-Light-xcursor
          Comment=Deepin Light Xcursor Theme
          EOF
          fi
        '';

        meta = {
          description = "Deepin Light Xcursor theme";
          homepage = "https://github.com/y0usaf/Cursors";
          license = pkgs.lib.licenses.mit;
        };
      };

      deepin-light-hyprcursor = pkgs.stdenv.mkDerivation {
        pname = "deepin-light-hyprcursor";
        version = "1.0.0";
        src = ./deepin-light/hyprcursor;

        sourceRoot = ".";
        dontFixTimestamps = true;

        installPhase = ''
          mkdir -p $out/share/icons/Deepin-Light-hyprcursor
          if [ -d "$src/hyprcursors" ]; then
            cp -r $src/hyprcursors $out/share/icons/Deepin-Light-hyprcursor/
          fi
          if [ -f "$src/manifest.hl" ]; then
            cp $src/manifest.hl $out/share/icons/Deepin-Light-hyprcursor/
          else
            printf '%s\n' 'name = Deepin-Light-hyprcursor' \
              'description = Deepin Light Cursor Theme for Hyprland' \
              'version = 1.0' \
              'cursors_directory = hyprcursors' > $out/share/icons/Deepin-Light-hyprcursor/manifest.hl
          fi
        '';

        meta = {
          description = "Deepin Light Hyprland cursor theme";
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
          mkdir -p $out/share/icons/Raccoin-xcursor
          cp -r $src/cursors $out/share/icons/Raccoin-xcursor/
          cp $src/index.theme $out/share/icons/Raccoin-xcursor/
        '';

        meta = {
          description = "Raccoin Xcursor theme";
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
          mkdir -p $out/share/icons/SSB-xcursor
          if [ -d "$src/cursors" ]; then
            cp -r $src/cursors $out/share/icons/SSB-xcursor/
          fi
          if [ -f "$src/index.theme" ]; then
            cp $src/index.theme $out/share/icons/SSB-xcursor/
          else
            cat > $out/share/icons/SSB-xcursor/index.theme << EOF
            [Icon Theme]
            Name=SSB-xcursor
            Comment=Super Smash Bros Ultimate Xcursor Theme
            EOF
          fi
        '';

        meta = {
          description = "Super Smash Bros Ultimate Xcursor theme";
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
