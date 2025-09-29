{
  description = "Fabric Bar Example";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/24.11";
    unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
    fabric.url = "github:Makesesama/fabric";
    home-manager.url = "github:nix-community/home-manager";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    {
      self,
      nixpkgs,
      unstable,
      utils,
      fabric,
      ...
    }:
    utils.lib.eachDefaultSystem (
      system:
      let
        # Dependencies want from nixpkgs unstable as an overlay
        unstable-overlay = final: prev: { basedpyright = unstable.legacyPackages.${system}.basedpyright; };
        # Fabric overlay
        fabric-overlay = fabric.overlays.${system}.default;
        # Apply both overlays
        pkgs = (nixpkgs.legacyPackages.${system}.extend fabric-overlay).extend unstable-overlay;
      in
      {
        formatter = pkgs.nixfmt-rfc-style;
        devShells.default = pkgs.callPackage ./nix/shell.nix { inherit pkgs; };
        packages = {
          default = pkgs.callPackage ./nix/derivation.nix { inherit (pkgs) lib python3Packages; };
          makku = pkgs.writeShellScriptBin "makku" ''
            dbus-send --session --print-reply --dest=org.Fabric.fabric.bar  /org/Fabric/fabric org.Fabric.fabric.Evaluate string:"finder.show()" > /dev/null 2>&1
          '';
        };
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/bar";
        };
      }
    )
    // {
      homeManagerModules = {
        makku-bar =
        {
          config,
          lib,
          pkgs,
          ...
        }:
        let
          cfg = config.services.makku-bar;

          settingsFormat = pkgs.formats.yaml { };
        in
        {
          options.services.makku-bar = {
            enable = lib.mkEnableOption "makku-bar status bar";

            package = lib.mkOption {
              type = lib.types.package;
              default = self.packages.${pkgs.system}.default;
              description = "The makku-bar package to use.";
            };

            settings = lib.mkOption {
              type = lib.types.submodule {
                options = {
                  vinyl = {
                    enable = lib.mkOption {
                      type = lib.types.bool;
                      default = false;
                    };
                  };
                  battery = {
                    enable = lib.mkOption {
                      type = lib.types.bool;
                      default = false;
                    };
                  };
                  height = lib.mkOption {
                    type = lib.types.int;
                    default = 40;
                    description = "Height of the status bar in pixels";
                  };
                  window_title = {
                    enable = lib.mkOption {
                      type = lib.types.bool;
                      default = true;
                      description = "Whether to show the window title in the center of the bar";
                    };
                  };
                };
              };
              default = {
                vinyl.enable = false;
                battery.enable = false;
                height = 40;
                window_title.enable = true;
              };
            };
          };

          config = lib.mkIf config.services.makku-bar.enable {
            systemd.user.services.makku-bar =
              let
                configFile = settingsFormat.generate "config.yaml" cfg.settings;
              in
              {
                Unit = {
                  Description = "Makku Status Bar";
                  After = [ "graphical-session.target" ];
                };

                Service = {
                  ExecStart = "${config.services.makku-bar.package}/bin/bar --config ${configFile}";
                  Restart = "on-failure";
                };

                Install = {
                  WantedBy = [ "default.target" ];
                };
              };
          };
        };
        stylix-makku-bar = import ./nix/stylix/hm.nix;
      };
    };
}
