"""Position size and trade-plan math.

Usage:
  python risk.py --capital 1000 --risk 1 --entry 2230 --stop 2170 --target 2350
"""
import argparse
import json


def plan(capital, risk_pct, entry, stop, target=None, fee_pct=0.1, max_leverage=1.0):
    if entry == stop:
        raise ValueError("سعر الدخول يساوي وقف الخسارة")
    side = "long" if stop < entry else "short"
    risk_amount = capital * risk_pct / 100
    # Each unit loses |entry - stop| plus round-trip fees if stopped out
    per_unit_loss = abs(entry - stop) + (entry + stop) * fee_pct / 100
    qty = risk_amount / per_unit_loss
    notional = qty * entry
    leverage_needed = notional / capital

    out = {
        "side": side,
        "risk_amount": round(risk_amount, 2),
        "quantity": round(qty, 6),
        "position_value": round(notional, 2),
        "leverage_needed": round(leverage_needed, 2),
        "stop_distance_pct": round(abs(entry - stop) / entry * 100, 2),
        "warnings": [],
    }
    if leverage_needed > max_leverage:
        capped_qty = capital * max_leverage / entry
        out["warnings"].append(
            f"الحجم يتطلب رافعة {leverage_needed:.1f}x. بدون رافعة الحد الأقصى {capped_qty:.6f} "
            f"وستكون المخاطرة الفعلية أقل من {risk_pct}%"
        )
    if risk_pct > 2:
        out["warnings"].append("المخاطرة أكبر من 2% من رأس المال في صفقة واحدة")

    if target is not None:
        if (side == "long" and target <= entry) or (side == "short" and target >= entry):
            raise ValueError("الهدف في الاتجاه الخاطئ بالنسبة للدخول")
        per_unit_gain = abs(target - entry) - (entry + target) * fee_pct / 100
        rr = per_unit_gain / per_unit_loss
        out.update(
            {
                "reward_amount": round(per_unit_gain * qty, 2),
                "risk_reward": round(rr, 2),
                "breakeven_win_rate_pct": round(100 / (1 + rr), 1) if rr > 0 else None,
            }
        )
        if rr < 2:
            out["warnings"].append(f"نسبة العائد للمخاطرة {rr:.2f} أقل من 2")
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--capital", type=float, required=True)
    p.add_argument("--risk", type=float, default=1.0, help="نسبة المخاطرة من رأس المال %%")
    p.add_argument("--entry", type=float, required=True)
    p.add_argument("--stop", type=float, required=True)
    p.add_argument("--target", type=float)
    p.add_argument("--fee", type=float, default=0.1, help="عمولة كل جهة %%")
    p.add_argument("--max-leverage", type=float, default=1.0)
    a = p.parse_args()
    print(json.dumps(plan(a.capital, a.risk, a.entry, a.stop, a.target, a.fee, a.max_leverage),
                     ensure_ascii=False, indent=2))
