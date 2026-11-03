import base64
import io

import matplotlib.pyplot as plt

# Backend sem janela: no servidor os gráficos são gerados apenas como imagem
plt.switch_backend("Agg")


def figura_para_base64(fig):
    """Converte uma figura do matplotlib/seaborn em PNG (base64) para exibir em uma tag <img>."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("ascii")
