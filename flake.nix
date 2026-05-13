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
      inherit (pkgs) lib;

      capitalize = s: let
        first = builtins.substring 0 1 s;
        rest = builtins.substring 1 (-1) s;
      in
        (lib.toUpper first) + rest;

      mkCursorThemePassthru = {
        id,
        xcursorPackage ? null,
        xcursorName ? null,
        hyprcursorPackage ? null,
        hyprcursorName ? null,
      }: let
        hasXcursor = xcursorPackage != null && xcursorName != null;
        hasHyprcursor = hyprcursorPackage != null && hyprcursorName != null;

        packages =
          lib.optional hasXcursor xcursorPackage
          ++ lib.optional hasHyprcursor hyprcursorPackage;

        xcursorSessionVariables = lib.optionalAttrs hasXcursor {
          XCURSOR_THEME = xcursorName;
        };
        hyprcursorSessionVariables = lib.optionalAttrs hasHyprcursor {
          HYPRCURSOR_THEME = hyprcursorName;
        };
        sessionVariables = xcursorSessionVariables // hyprcursorSessionVariables;

        gtkSettings = lib.optionalAttrs hasXcursor {
          "gtk-cursor-theme-name" = xcursorName;
        };

        mkSessionVariables = {
          xcursorSize ? null,
          hyprcursorSize ? null,
        }:
          sessionVariables
          // lib.optionalAttrs (hasXcursor && xcursorSize != null) {
            XCURSOR_SIZE = toString xcursorSize;
          }
          // lib.optionalAttrs (hasHyprcursor && hyprcursorSize != null) {
            HYPRCURSOR_SIZE = toString hyprcursorSize;
          };

        mkGtkSettings = size:
          gtkSettings
          // lib.optionalAttrs hasXcursor {
            "gtk-cursor-theme-size" = toString size;
          };

        cursorTheme =
          {
            inherit id packages sessionVariables mkSessionVariables;
          }
          // lib.optionalAttrs hasXcursor {
            xcursor = {
              package = xcursorPackage;
              name = xcursorName;
              themeName = xcursorName;
              sessionVariables = xcursorSessionVariables;
              mkSessionVariables = size:
                xcursorSessionVariables
                // {
                  XCURSOR_SIZE = toString size;
                };
              inherit gtkSettings mkGtkSettings;
            };
            xcursorPackage = xcursorPackage;
            xcursorThemeName = xcursorName;
            inherit gtkSettings mkGtkSettings;
          }
          // lib.optionalAttrs hasHyprcursor {
            hyprcursor = {
              package = hyprcursorPackage;
              name = hyprcursorName;
              themeName = hyprcursorName;
              sessionVariables = hyprcursorSessionVariables;
              mkSessionVariables = size:
                hyprcursorSessionVariables
                // {
                  HYPRCURSOR_SIZE = toString size;
                };
            };
            hyprcursorPackage = hyprcursorPackage;
            hyprcursorThemeName = hyprcursorName;
          };
      in
        {
          inherit cursorTheme;
          cursorThemeId = id;
          cursorPackages = packages;
          cursorSessionVariables = sessionVariables;
          mkCursorSessionVariables = mkSessionVariables;
        }
        // lib.optionalAttrs hasXcursor {
          xcursorPackage = xcursorPackage;
          xcursorThemeName = xcursorName;
          gtkCursorSettings = gtkSettings;
          mkGtkCursorSettings = mkGtkSettings;
        }
        // lib.optionalAttrs hasHyprcursor {
          hyprcursorPackage = hyprcursorPackage;
          hyprcursorThemeName = hyprcursorName;
        };

      mkCursorThemePackage = args @ {
        id,
        description ? "${id} cursor theme",
        homepage ? "https://github.com/y0usaf/Cursors",
        license ? lib.licenses.mit,
        ...
      }: let
        passthru = mkCursorThemePassthru (builtins.removeAttrs args ["description" "homepage" "license"]);
      in
        pkgs.symlinkJoin {
          name = "${id}-cursor-theme";
          paths = passthru.cursorTheme.packages;
          inherit passthru;
          meta = {
            inherit description homepage license;
            platforms = lib.platforms.all;
          };
        };

      popucomXcursorName = color: "Popucom-${capitalize color}-xcursor";
      popucomHyprcursorName = color: "Popucom-${capitalize color}-hyprcursor";

      mkPopucomXcursor = color: let
        themeName = popucomXcursorName color;
      in
        pkgs.stdenv.mkDerivation {
          pname = "popucom-${color}-xcursor";
          version = "1.0.0";
          src = ./popucom/${color}/xcursor;
          sourceRoot = ".";
          installPhase = ''
            mkdir -p $out/share/icons/${themeName}
            cp -r $src/cursors $out/share/icons/${themeName}/
            cp $src/index.theme $out/share/icons/${themeName}/
          '';
          meta.description = "Popucom ${capitalize color} animated Xcursor theme";
        };

      mkPopucomHyprcursor = color: let
        themeName = popucomHyprcursorName color;
      in
        pkgs.stdenv.mkDerivation {
          pname = "popucom-${color}-hyprcursor";
          version = "1.0.0";
          src = ./popucom/${color}/hyprcursor;
          sourceRoot = ".";
          dontFixTimestamps = true;
          installPhase = ''
            mkdir -p $out/share/icons/${themeName}
            cp -r $src/hyprcursors $out/share/icons/${themeName}/
            cp $src/manifest.hl $out/share/icons/${themeName}/
          '';
          meta.description = "Popucom ${capitalize color} animated Hyprland cursor theme";
        };

      earendilXcursorName = variant: "Earendil-${capitalize variant}-xcursor";
      earendilHyprcursorName = variant: "Earendil-${capitalize variant}-hyprcursor";

      mkEarendilXcursor = variant: let
        themeName = earendilXcursorName variant;
      in
        pkgs.stdenv.mkDerivation {
          pname = "earendil-${variant}-xcursor";
          version = "1.0.0";
          src = ./. + "/earendil-${variant}/xcursor";
          sourceRoot = ".";

          installPhase = ''
            runHook preInstall

            outDir="$out/share/icons/${themeName}"
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

      mkEarendilHyprcursor = variant: let
        themeName = earendilHyprcursorName variant;
      in
        pkgs.stdenv.mkDerivation {
          pname = "earendil-${variant}-hyprcursor";
          version = "1.0.0";
          src = ./. + "/earendil-${variant}/hyprcursor";
          sourceRoot = ".";
          dontFixTimestamps = true;

          installPhase = ''
            runHook preInstall

            outDir="$out/share/icons/${themeName}"
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
          {
            name = "popucom-${color}-xcursor";
            value = mkPopucomXcursor color;
          }
          {
            name = "popucom-${color}-hyprcursor";
            value = mkPopucomHyprcursor color;
          }
        ])
        popucomColors);

      raccoinVariantNames = {
        default = "Default";
        dark = "Dark";
        bw = "BW";
        "black-outline" = "Black-Outline";
      };

      raccoinXcursorName = variant: "Raccoin-${raccoinVariantNames.${variant}}-xcursor";
      raccoinHyprcursorName = variant: "Raccoin-${raccoinVariantNames.${variant}}-hyprcursor";

      mkRaccoinXcursor = variant: let
        variantName = raccoinVariantNames.${variant};
        themeName = raccoinXcursorName variant;
      in
        pkgs.stdenv.mkDerivation {
          pname = "raccoin-${variant}-xcursor";
          version = "1.0.0";
          src = ./. + "/themes/raccoin/${variant}/xcursor";
          sourceRoot = ".";

          installPhase = ''
            mkdir -p "$out/share/icons/${themeName}"
            cp -r "$src/cursors" "$out/share/icons/${themeName}/"
            cp "$src/index.theme" "$out/share/icons/${themeName}/"
          '';

          meta = {
            description = "Raccoin ${variantName} Xcursor theme";
            homepage = "https://github.com/y0usaf/Cursors";
            license = lib.licenses.mit;
          };
        };

      mkRaccoinHyprcursor = variant: let
        variantName = raccoinVariantNames.${variant};
        themeName = raccoinHyprcursorName variant;
      in
        pkgs.stdenv.mkDerivation {
          pname = "raccoin-${variant}-hyprcursor";
          version = "1.0.0";
          src = ./. + "/themes/raccoin/${variant}/hyprcursor";
          sourceRoot = ".";
          dontFixTimestamps = true;

          installPhase = ''
            mkdir -p "$out/share/icons/${themeName}"
            cp -r "$src/hyprcursors" "$out/share/icons/${themeName}/"
            cp "$src/manifest.hl" "$out/share/icons/${themeName}/"
          '';

          meta = {
            description = "Raccoin ${variantName} Hyprland cursor theme";
            homepage = "https://github.com/y0usaf/Cursors";
            license = lib.licenses.mit;
          };
        };

      raccoinVariants = ["default" "dark" "bw" "black-outline"];

      raccoinPackages = builtins.listToAttrs (builtins.concatMap (variant: [
          {
            name = "raccoin-${variant}-xcursor";
            value = mkRaccoinXcursor variant;
          }
          {
            name = "raccoin-${variant}-hyprcursor";
            value = mkRaccoinHyprcursor variant;
          }
        ])
        raccoinVariants);

      basePackages =
        popucomPackages
        // raccoinPackages
        // rec {
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
                printf '%s\n' '[Icon Theme]' \
                  'Name=Deepin-Dark-xcursor' \
                  'Comment=Deepin Dark Xcursor Theme' > $out/share/icons/Deepin-Dark-xcursor/index.theme
              fi
            '';

            meta = {
              description = "Deepin Dark Xcursor theme";
              homepage = "https://github.com/y0usaf/Cursors";
              license = lib.licenses.mit;
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
              license = lib.licenses.mit;
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
                printf '%s\n' '[Icon Theme]' \
                  'Name=Deepin-Light-xcursor' \
                  'Comment=Deepin Light Xcursor Theme' > $out/share/icons/Deepin-Light-xcursor/index.theme
              fi
            '';

            meta = {
              description = "Deepin Light Xcursor theme";
              homepage = "https://github.com/y0usaf/Cursors";
              license = lib.licenses.mit;
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
              license = lib.licenses.mit;
            };
          };

          # Backwards-compatible aliases for the default Raccoin colour.
          raccoin-xcursor = raccoinPackages."raccoin-default-xcursor";
          raccoin-hyprcursor = raccoinPackages."raccoin-default-hyprcursor";

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
                printf '%s\n' '[Icon Theme]' \
                  'Name=SSB-xcursor' \
                  'Comment=Super Smash Bros Ultimate Xcursor Theme' > $out/share/icons/SSB-xcursor/index.theme
              fi
            '';

            meta = {
              description = "Super Smash Bros Ultimate Xcursor theme";
              homepage = "https://github.com/y0usaf/Cursors";
              license = lib.licenses.mit;
            };
          };

          earendil-dark-xcursor = mkEarendilXcursor "dark";
          earendil-light-xcursor = mkEarendilXcursor "light";
          earendil-dark-hyprcursor = mkEarendilHyprcursor "dark";
          earendil-light-hyprcursor = mkEarendilHyprcursor "light";
        };

      popucomThemePackages = builtins.listToAttrs (map (color: {
          name = "popucom-${color}";
          value = mkCursorThemePackage {
            id = "popucom-${color}";
            description = "Popucom ${capitalize color} animated cursor theme";
            xcursorPackage = basePackages."popucom-${color}-xcursor";
            xcursorName = popucomXcursorName color;
            hyprcursorPackage = basePackages."popucom-${color}-hyprcursor";
            hyprcursorName = popucomHyprcursorName color;
          };
        })
        popucomColors);

      raccoinThemePackages = builtins.listToAttrs (map (variant: {
          name = "raccoin-${variant}";
          value = mkCursorThemePackage {
            id = "raccoin-${variant}";
            description = "Raccoin ${raccoinVariantNames.${variant}} cursor theme";
            xcursorPackage = basePackages."raccoin-${variant}-xcursor";
            xcursorName = raccoinXcursorName variant;
            hyprcursorPackage = basePackages."raccoin-${variant}-hyprcursor";
            hyprcursorName = raccoinHyprcursorName variant;
          };
        })
        raccoinVariants);

      combinedPackages =
        popucomThemePackages
        // raccoinThemePackages
        // {
          deepin-dark = mkCursorThemePackage {
            id = "deepin-dark";
            description = "Deepin Dark cursor theme";
            xcursorPackage = basePackages.deepin-dark-xcursor;
            xcursorName = "Deepin-Dark-xcursor";
            hyprcursorPackage = basePackages.deepin-dark-hyprcursor;
            hyprcursorName = "Deepin-Dark-hyprcursor";
          };

          deepin-light = mkCursorThemePackage {
            id = "deepin-light";
            description = "Deepin Light cursor theme";
            xcursorPackage = basePackages.deepin-light-xcursor;
            xcursorName = "Deepin-Light-xcursor";
            hyprcursorPackage = basePackages.deepin-light-hyprcursor;
            hyprcursorName = "Deepin-Light-hyprcursor";
          };

          earendil-dark = mkCursorThemePackage {
            id = "earendil-dark";
            description = "Earendil Dark cursor theme";
            homepage = "https://earendil.com";
            xcursorPackage = basePackages.earendil-dark-xcursor;
            xcursorName = earendilXcursorName "dark";
            hyprcursorPackage = basePackages.earendil-dark-hyprcursor;
            hyprcursorName = earendilHyprcursorName "dark";
          };

          earendil-light = mkCursorThemePackage {
            id = "earendil-light";
            description = "Earendil Light cursor theme";
            homepage = "https://earendil.com";
            xcursorPackage = basePackages.earendil-light-xcursor;
            xcursorName = earendilXcursorName "light";
            hyprcursorPackage = basePackages.earendil-light-hyprcursor;
            hyprcursorName = earendilHyprcursorName "light";
          };

          raccoin = mkCursorThemePackage {
            id = "raccoin";
            description = "Raccoin Default cursor theme";
            xcursorPackage = basePackages.raccoin-xcursor;
            xcursorName = raccoinXcursorName "default";
            hyprcursorPackage = basePackages.raccoin-hyprcursor;
            hyprcursorName = raccoinHyprcursorName "default";
          };

          ssb = mkCursorThemePackage {
            id = "ssb";
            description = "Super Smash Bros Ultimate Xcursor theme";
            xcursorPackage = basePackages.ssb-xcursor;
            xcursorName = "SSB-xcursor";
          };
        };
    in
      basePackages
      // combinedPackages
      // {
        default = combinedPackages."deepin-dark";
      });
  };
}
