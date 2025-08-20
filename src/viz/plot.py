from __future__ import annotations
from typing import List, Optional
import matplotlib.pyplot as plt

def plot_price_with_sma(times: List[str], closes: List[float],
                        sma_fast: Optional[List[float]] = None,
                        sma_slow: Optional[List[float]] = None,
                        title: str = "Price & SMA"):
    fig, ax = plt.subplots()
    ax.plot(closes, label="Close")
    if sma_fast: ax.plot(range(len(closes)-len(sma_fast), len(closes)), sma_fast, label="SMA fast")
    if sma_slow: ax.plot(range(len(closes)-len(sma_slow), len(closes)), sma_slow, label="SMA slow")
    ax.legend(); ax.set_title(title)
    fig.tight_layout()
    return fig

def save_fig(fig, path: str):
    fig.savefig(path, dpi=120)
