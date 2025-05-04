{
  description = "Fabric Bar Example";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/24.05";
    unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
    fabric.url = "github:wholikeel/fabric-nix";
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
        devShells.default = pkgs.callPackage ./shell.nix { inherit pkgs; };
        packages.default = pkgs.callPackage ./derivation.nix { inherit (pkgs) lib python3Packages; };
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/bar";
        };
      }
    )
    // {
      homeManagerModules.makku-bar =
        {
          config,
          lib,
          pkgs,
          ...
        }:
        {
          options.services.makku-bar = {
            enable = lib.mkEnableOption "makku-bar status bar";

            package = lib.mkOption {
              type = lib.types.package;
              default = pkgs.callPackage ./derivation.nix { inherit (pkgs) lib python3Packages; };
              description = "The makku-bar package to use.";
            };
          };

          config = lib.mkIf config.services.makku-bar.enable {
            systemd.user.services.makku-bar = {
              Unit = {
                Description = "Makku Status Bar";
                After = [ "graphical-session.target" ];
              };

              Service = {
                ExecStart = "${config.services.makku-bar.package}/bin/bar";
                Restart = "on-failure";
              };

              Install = {
                WantedBy = [ "default.target" ];
              };
            };
          };
        };
    };
}
