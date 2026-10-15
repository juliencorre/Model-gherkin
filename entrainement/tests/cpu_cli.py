"""`gherkin-ft` pour les tests sur CPU : même CLI, avec le noyau Triton de TRL remplacé (voir cpu_kernel.py).

Utilisé comme commande d'entraînement par les tests de l'interface (processus séparé).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cpu_kernel  # noqa: E402

cpu_kernel.install()

from gherkin_ft.cli import main  # noqa: E402

sys.exit(main())
