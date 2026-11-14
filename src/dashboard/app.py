from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict
import streamlit as st
import subprocess, tempfile
import pandas as pd  # we use pandas in multiple places below

# Local imports from your project
from src.data.providers.alpaca import fetch_bars
from src.strategy.sma import sma

try:
    # Optional: fake client for mock mode
    from src.sim.providers.fake_alpaca import FakeREST
except Exception:
    FakeREST = None  # type: ignore


# ---------- Helpers ----------
def load_audit(path: str = "logs/audit.jsonl") -> List[Dict]:
    p = Path(path)
    if not p.exists():
        return []
    out: List[Dict] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def equity_from_backtest_jsonl(path: str) -> List[float]:
    """
    Very lightweight equity curve builder from backtest jsonl trades:
    Each line is expected to be a trade dict: {ts, side, price, notional, symbol}
    """
    p = Path(path)
    if not p.exists():
        return []

    trades: List[Dict] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
            if {"ts","side","price","notional"}.issubset(rec):
                trades.append(rec)
        except Exception:
            pass

    equity = 100_000.0
    curve = [equity]
    by_sym: Dict[str, List[Dict]] = {}
    for t in trades:
        by_sym.setdefault(t.get("symbol", "GEN"), []).append(t)

    for sym, events in by_sym.items():
        open_buy = None
        for ev in events:
            if ev["side"] == "buy" and open_buy is None:
                open_buy = ev
            elif ev["side"] == "sell" and open_buy is not None:
                shares = open_buy["notional"] / open_buy["price"] if open_buy["price"] else 0
                pnl = (ev["price"] - open_buy["price"]) * shares
                equity += pnl
                curve.append(equity)
                open_buy = None
    return curve


# ---------- UI ----------
st.set_page_config(page_title="Algo Trading Bot", layout="wide")
st.title("Algo Trading Bot Dashboard")

# Sidebar controls
st.sidebar.header("Controls")
symbol = st.sidebar.text_input("Symbol", value="AAPL")
limit = st.sidebar.number_input("Bars to load", min_value=10, max_value=2000, value=60, step=10)
fast = st.sidebar.number_input("SMA Fast", min_value=2, max_value=100, value=5, step=1)
slow = st.sidebar.number_input("SMA Slow", min_value=3, max_value=300, value=20, step=1)
mock = st.sidebar.checkbox("Mock mode (FakeREST)", value=True)

st.sidebar.markdown("---")
st.sidebar.header("Run mode")
run_mode = st.sidebar.selectbox(
    "Mode",
    options=["mock", "paper", "live"],
    index=0 if mock else 1,
    help="mock = FakeREST + fake brackets; paper/live need keys and ENABLE_TRADING=true",
)
risk = st.sidebar.number_input("Risk per trade (fraction)", min_value=0.001, max_value=0.05, value=0.005, step=0.001, format="%.3f")
stop = st.sidebar.number_input("Stop loss %", min_value=0.005, max_value=0.20, value=0.03, step=0.005, format="%.3f")
take = st.sidebar.number_input("Take profit %", min_value=0.005, max_value=0.50, value=0.05, step=0.005, format="%.3f")
max_pos = st.sidebar.number_input("Max positions", min_value=1, max_value=10, value=2, step=1)

run_now = st.sidebar.button("Run Tick Now")

if run_now:
    st.subheader("Run Tick Result")
    # Build command to call your CLI inside the same container
    # Universe is the single symbol from the sidebar
    cmd = [
        "python", "-m", "src.app", "run-daily",
        "--universe", symbol,
        "--limit", str(int(limit)),
        "--fast", str(int(fast)),
        "--slow", str(int(slow)),
        "--risk", str(float(risk)),
        "--stop", str(float(stop)),
        "--take", str(float(take)),
        "--max-pos", str(int(max_pos)),
        "--mode", run_mode,
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        st.code(" ".join(cmd))
        if res.stdout:
            st.success("STDOUT:")
            st.code(res.stdout)
        if res.stderr:
            st.warning("STDERR:")
            st.code(res.stderr)
    except Exception as e:
        st.error(f"Error running tick: {e}")

    # Reload audit after running
    audit = load_audit()
    if audit:
        st.write("Latest audit events:")
        tail_df = pd.DataFrame(audit[-10:])
        st.dataframe(tail_df)
    else:
        st.info("No audit log yet after run.")

# Load bars
client = FakeREST() if (mock and FakeREST is not None) else None
bars = fetch_bars(symbol=symbol, limit=int(limit), client=client)
closes = [b.c for b in bars]
times = [str(b.t) for b in bars]

# Plot price + SMAs
st.subheader(f"Price & SMA — {symbol}")
if closes:
    sf = sma(closes, int(fast))
    ss = sma(closes, int(slow))
    # Streamlit line_chart expects dict[len]; pad SMA to align visually
    df = pd.DataFrame({"close": closes}, index=times)
    # align SMA series to same length by padding with None
    pad_f = [None] * (len(closes) - len(sf)) + sf
    pad_s = [None] * (len(closes) - len(ss)) + ss
    df["sma_fast"] = pad_f
    df["sma_slow"] = pad_s
    st.line_chart(df)
else:
    st.info("No data loaded yet.")

# Recent decisions from audit
st.subheader("Recent Decisions (from audit log)")
audit = load_audit()
if audit:
    # Show last 50 events
    last = audit[-50:]
    # pretty small table
    st.dataframe(pd.DataFrame(last))
else:
    st.info("No audit log yet. Run the bot to generate decisions.")

# Equity curve from backtest (optional)
st.subheader("Equity Curve (Backtest JSONL)")

# Path-based input (default path)
backtest_path = st.text_input("Backtest JSONL path", value="logs/backtest_AAPL.jsonl")

# OR upload a JSONL here
uploaded = st.file_uploader("Upload backtest JSONL", type=["jsonl"])

curve = []
if st.button("Load Equity Curve"):
    tmp_path = None
    if uploaded is not None:
        # Save to a temporary file so equity loader can read it
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as tf:
            tf.write(uploaded.read())
            tmp_path = tf.name
        use_path = tmp_path
    else:
        use_path = backtest_path

    try:
        curve = equity_from_backtest_jsonl(use_path)
        if curve:
            st.line_chart(curve)
        else:
            st.warning("No equity data. Provide a valid backtest jsonl with trade events.")
    except Exception as e:
        st.error(f"Failed to load equity curve: {e}")