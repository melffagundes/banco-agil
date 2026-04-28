import pandas as pd
import os


def ler_csv_seguro(path: str) -> pd.DataFrame:
    """Lê um CSV com tratamento de erros. Retorna DataFrame vazio se falhar."""
    try:
        if not os.path.exists(path):
            return pd.DataFrame()
        return pd.read_csv(path, dtype=str)
    except Exception as e:
        print(f"Erro ao ler CSV '{path}': {e}")
        return pd.DataFrame()


def escrever_csv_seguro(df: pd.DataFrame, path: str) -> bool:
    """Escreve DataFrame em CSV com tratamento de erros. Retorna True se bem-sucedido."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        return True
    except Exception as e:
        print(f"Erro ao escrever CSV '{path}': {e}")
        return False
