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

    popucomColors = ["pink" "green" "blue" "yellow" "red" "orange" "cyan" "purple" "grey" "black" "inverted"];
    raccoinVariants = ["default" "dark" "bw" "black-outline"];

    themeIds =
      ["deepin-dark" "deepin-light" "earendil-dark" "earendil-light"]
      ++ map (color: "popucom-${color}") popucomColors
      ++ map (variant: "raccoin-${variant}") raccoinVariants
      ++ ["ssb"];

    extraMeta = {
      ssb.description = "Super Smash Bros Ultimate Xcursor theme";
      earendil-dark.homepage = "https://earendil.com";
      earendil-light.homepage = "https://earendil.com";
    };
  in {
    packages = forAllSystems (system: let
      pkgs = import nixpkgs {inherit system;};
      inherit (pkgs) lib;

      getMeta = id: builtins.fromJSON (builtins.readFile (./. + "/themes/${id}/theme.json"));

      mkOutput = id: kind:
        pkgs.runCommand "${id}-${kind}-1.0.0" {
          nativeBuildInputs = [pkgs.jq pkgs.python3 pkgs.hyprcursor];
          scripts = ./scripts;
        } ''
          bash "$scripts/build-theme.sh" ${kind} ${./. + "/themes/${id}"} "$out"
        '';

      mkTheme = id: let
        meta = getMeta id;
        xcursorName = meta.name;
        hyprcursorName = meta.hyprcursor.name or null;
        xcursor = mkOutput id "xcursor";
        hyprcursorPackage = mkOutput id "hyprcursor";
        hasHyprcursor = hyprcursorName != null;

        sessionVariables =
          {XCURSOR_THEME = xcursorName;}
          // lib.optionalAttrs (hyprcursorName != null) {HYPRCURSOR_THEME = hyprcursorName;};
        gtkSettings = {"gtk-cursor-theme-name" = xcursorName;};

        mkSessionVariables = {
          xcursorSize ? null,
          hyprcursorSize ? null,
        }:
          sessionVariables
          // lib.optionalAttrs (xcursorSize != null) {XCURSOR_SIZE = toString xcursorSize;}
          // lib.optionalAttrs (hasHyprcursor && hyprcursorSize != null) {
            HYPRCURSOR_SIZE = toString hyprcursorSize;
          };

        title = lib.replaceStrings ["-"] [" "] (lib.removeSuffix "-xcursor" xcursorName);
      in
        pkgs.symlinkJoin {
          name = "${id}-cursor-theme";
          paths = [xcursor] ++ lib.optional hasHyprcursor hyprcursorPackage;
          passthru = {
            cursorPackages = [xcursor] ++ lib.optional hasHyprcursor hyprcursorPackage;
            cursorSessionVariables = sessionVariables;
            mkCursorSessionVariables = mkSessionVariables;
            xcursorPackage = xcursor;
            xcursorThemeName = xcursorName;
            gtkCursorSettings = gtkSettings;
            mkGtkCursorSettings = size: gtkSettings // {"gtk-cursor-theme-size" = toString size;};
          }
          // lib.optionalAttrs hasHyprcursor {
            inherit hyprcursorPackage;
            hyprcursorThemeName = hyprcursorName;
          };
          meta = {
            description = "${title} cursor theme";
            homepage = "https://github.com/y0usaf/cursors";
            license = lib.licenses.mit;
            platforms = lib.platforms.all;
          }
          // (extraMeta.${id} or {});
        };

      themes = builtins.listToAttrs (map (id: {
          name = id;
          value = mkTheme id;
        })
        themeIds);

      outputs = builtins.listToAttrs (builtins.concatMap (id: let
          meta = getMeta id;
        in
          [
            {
              name = "${id}-xcursor";
              value = mkOutput id "xcursor";
            }
          ]
          ++ lib.optional (meta ? hyprcursor) {
            name = "${id}-hyprcursor";
            value = mkOutput id "hyprcursor";
          })
        themeIds);
    in
      themes
      // outputs
      // {
        raccoin = themes.raccoin-default;
        raccoin-xcursor = outputs."raccoin-default-xcursor";
        raccoin-hyprcursor = outputs."raccoin-default-hyprcursor";
        default = themes.deepin-dark;
      });
  };
}
