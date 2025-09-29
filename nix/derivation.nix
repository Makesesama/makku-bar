{
  lib,
  python3Packages,
  gtk3,
  gtk-layer-shell,
  cairo,
  gobject-introspection,
  libdbusmenu-gtk3,
  gdk-pixbuf,
  gnome-bluetooth,
  cinnamon-desktop,
  wrapGAppsHook3,
  playerctl,
  webp-pixbuf-loader,
  notmuch,
  khal,
  emacs,
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
    gnome-bluetooth
    cinnamon-desktop
    gdk-pixbuf
    playerctl
    webp-pixbuf-loader
    notmuch
    khal
  ];

  dependencies = with python3Packages; [
    python-fabric
    pywayland
    pyyaml
    platformdirs
  ];
  doCheck = false;
  dontWrapGApps = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/${python3Packages.python.sitePackages}
    cp -r bar $out/${python3Packages.python.sitePackages}/

    # If you have any scripts to install
    mkdir -p $out/bin
    cp scripts/launcher.py $out/bin/bar
    chmod +x $out/bin/bar


    runHook postInstall
  '';

  preFixup = ''
    makeWrapperArgs+=("''${gappsWrapperArgs[@]}")
    makeWrapperArgs+=(--prefix PATH : ${lib.makeBinPath [ khal notmuch emacs ]})
  '';

  passthru = {
    inherit khal notmuch emacs;
  };

  meta = {
    changelog = "";
    description = ''
      Fabrix Bar Example
    '';
    homepage = "https://github.com/wholikeel/fabric";
    license = lib.licenses.agpl3Only;
  };
}
