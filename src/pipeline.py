"""Executa raw -> refined -> marts; interrompe ao primeiro erro."""

import subprocess
import sys

from ingest import ROOT


def main() -> None:
    for script in ("ingest.py", "refine.py", "marts.py"):
        print(f"\n=== Executando {script} ===", flush=True)
        subprocess.run(
            [sys.executable, str(ROOT / "src" / script)],
            cwd=ROOT,
            check=True,
        )
    print("\nPipeline concluido com sucesso.")


if __name__ == "__main__":
    main()
