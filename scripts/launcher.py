#!/usr/bin/env python3
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
site_packages_dir = os.path.join(
    script_dir,
    os.pardir,
    "lib",
    f"python{sys.version_info.major}.{sys.version_info.minor}",
    "site-packages",
)

if site_packages_dir not in sys.path:
    sys.path.insert(0, site_packages_dir)


from bar.main import *

sys.argv[0] = os.path.join(script_dir, os.path.basename(__file__))
sys.exit(main())
