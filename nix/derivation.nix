{
  lib,
  python3Packages,
  gtk3,
  gtk-layer-shell,
  cairo,
  gobject-introspection,
  libdbusmenu-gtk3,
  gdk-pixbuf,
  gnome,
  cinnamon,
  wrapGAppsHook3,
  playerctl,
  webp-pixbuf-loader,
  ...
}:

python3Packages.buildPythonApplication {
  pname = "fabric-nix-example";
  version = "0.0.1";
  pyproject = true;

  src = ../.;

  nativeBuildInputs = [
    wrapGAppsHook3
    gtk3
    gobject-introspection
    python3Packages.pygobject3
    cairo
    playerctl
  ];
  buildInputs = [
    libdbusmenu-gtk3
    gtk-layer-shell
    gnome.gnome-bluetooth
    cinnamon.cinnamon-desktop
    gdk-pixbuf
    playerctl
    webp-pixbuf-loader
  ];

  dependencies = with python3Packages; [
    python-fabric
    pywayland
  ];
  doCheck = false;
  dontWrapGApps = true;

  preFixup = ''
    makeWrapperArgs+=("''${gappsWrapperArgs[@]}")
  '';

  meta = {
    changelog = "";
    description = ''
      Fabrix Bar Example
    '';
    homepage = "https://github.com/wholikeel/fabric";
    license = lib.licenses.agpl3Only;
  };
}
