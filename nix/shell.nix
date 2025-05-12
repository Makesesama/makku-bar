{
  pkgs ? import <nixpkgs> { },
}:
pkgs.mkShell {
  name = "fabric-shell";
  buildInputs = with pkgs; [
    dbus
    wayland-scanner
  ];
  nativeBuildInputs = with pkgs; [
    pkg-config
  ];
  dbus = pkgs.dbus;
  packages = with pkgs; [
    ruff # Linter
    basedpyright # Language server

    # Required for Devshell
    gtk3
    gtk-layer-shell
    cairo
    gobject-introspection
    libdbusmenu-gtk3
    gdk-pixbuf
    gnome.gnome-bluetooth
    cinnamon.cinnamon-desktop
    wayland-scanner
    wayland
    wayland-protocols
    (python3.withPackages (
      ps: with ps; [
        setuptools
        wheel
        build
        python-fabric
        psutil
        pywayland
        python-lsp-server
        pylsp-mypy
        pyls-isort
        python-lsp-ruff
      ]
    ))
  ];
}
