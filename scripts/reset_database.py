# ==============================================================================
# ARQUIVO: scripts/reset_database.py
# O QUE FAZ: Apaga e recria as tabelas do banco de dados local
# AUTOR: Marcos Zambon
# DATA: 25/05/2026
# ==============================================================================

"""Script — Reset do Banco de Dados"""

import sys
import os

# Garante que o módulo raiz está no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.database.connection import engine
from src.infrastructure.database.models import Base


def reset():
    print("⚠️  Apagando todas as tabelas...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tabelas removidas.")

    print("🔧 Recriando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados resetado com sucesso.")


if __name__ == "__main__":
    confirmacao = input("Tem certeza? Todos os dados serão perdidos. [s/N]: ")
    if confirmacao.lower() == "s":
        reset()
    else:
        print("Operação cancelada.")
