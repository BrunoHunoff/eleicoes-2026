import base64
import io

import matplotlib.pyplot as plt

# Backend sem janela: no servidor os gráficos são gerados apenas como imagem
plt.switch_backend("Agg")


def formatar_numero(valor, casas=0):
    """Formata um número no padrão brasileiro (ex.: 1.234.567,89). Registrado nos templates como o filtro "numero"."""
    texto = f"{valor:,.{casas}f}"  # padrão americano, ex.: 1,234,567.89
    # Troca vírgula por ponto e ponto por vírgula; o "_" guarda as vírgulas no meio da troca
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def figura_para_base64(fig):
    """Converte uma figura do matplotlib/seaborn em PNG (base64) para exibir em uma tag <img>."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("ascii")
