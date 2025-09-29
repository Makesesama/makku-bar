{ config, lib, ... }:

let
  cfg = config.stylix.targets.makku-bar;
in
{
  options.stylix.targets.makku-bar.enable =
    config.lib.stylix.mkEnableTarget "Makku Bar" true;

  config = lib.mkIf (config.stylix.enable && cfg.enable) {
    services.makku-bar.settings.stylix = {
      enable = true;
      colors = {
        base00 = config.lib.stylix.colors.base00; # background
        base01 = config.lib.stylix.colors.base01; # lighter background
        base02 = config.lib.stylix.colors.base02; # selection background
        base03 = config.lib.stylix.colors.base03; # comments
        base04 = config.lib.stylix.colors.base04; # dark foreground
        base05 = config.lib.stylix.colors.base05; # foreground
        base06 = config.lib.stylix.colors.base06; # light foreground
        base07 = config.lib.stylix.colors.base07; # light background
        base08 = config.lib.stylix.colors.base08; # red
        base09 = config.lib.stylix.colors.base09; # orange
        base0A = config.lib.stylix.colors.base0A; # yellow
        base0B = config.lib.stylix.colors.base0B; # green
        base0C = config.lib.stylix.colors.base0C; # cyan
        base0D = config.lib.stylix.colors.base0D; # blue
        base0E = config.lib.stylix.colors.base0E; # purple
        base0F = config.lib.stylix.colors.base0F; # brown
      };
      fonts = {
        serif = config.stylix.fonts.serif.name;
        sansSerif = config.stylix.fonts.sansSerif.name;
        monospace = config.stylix.fonts.monospace.name;
        sizes = {
          desktop = config.stylix.fonts.sizes.desktop;
          applications = config.stylix.fonts.sizes.applications;
          terminal = config.stylix.fonts.sizes.terminal;
          popups = config.stylix.fonts.sizes.popups;
        };
      };
    };
  };
}