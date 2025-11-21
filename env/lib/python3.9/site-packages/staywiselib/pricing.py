from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def D(value):
    """Helper: Always return a properly rounded Decimal."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ======================================================
  #  FESTIVAL DISCOUNT
# ======================================================
def apply_festival_discount(price, event=None):
    if not isinstance(price, Decimal):
        price = D(price)

    discounts = {
        "Christmas": D("0.15"),
        "NewYear": D("0.20"),
        "Diwali": D("0.10"),
    }

    discount = discounts.get(event, D("0"))
    discounted_price = price * (D("1") - discount)
    reason = f"Festival: {event}" if event in discounts else None

    return discounted_price, discount * 100, reason


# ======================================================
 #WEEKEND DISCOUNT
# ======================================================
def apply_weekend_discount(price):
    if not isinstance(price, Decimal):
        price = D(price)

    if datetime.today().weekday() in [5, 6]:  # Saturday or Sunday
        discounted = price * D("0.9")
        return discounted, D("10"), "Weekend Offer"
    else:
        return price, D("0"), None


# ======================================================
#  LONG-STAY DISCOUNT
# ======================================================
def apply_longstay_discount(price, days):
    """
    Apply discount for longer stays.
    ≥3 days → 5% off
    ≥7 days → 10% off
    """
    if not isinstance(price, Decimal):
        price = D(price)

    discount = D("0")
    reason = None

    if days >= 7:
        discount = D("0.10")
        reason = "Long-Stay (7+ days)"
    elif days >= 3:
        discount = D("0.05")
        reason = "Long-Stay (3+ days)"

    discounted_price = price * (D("1") - discount)
    return discounted_price, discount * 100, reason


# ======================================================
#  FINAL COMBINED CALCULATION
# ======================================================
def calculate_final_price(base_price, event=None, days=1):
    """
    Safely apply Festival + Weekend + Long-Stay discounts.
    Returns dict:
      {
        'final_price': 4.5,
        'total_discount_percent': 15.0,
        'total_discount_amount': 0.75,
        'discount_reason': 'Festival: Diwali + Long-Stay (3+ days)'
      }
    """
    if not isinstance(base_price, Decimal):
        base_price = D(base_price)

    # Step 1: Festival
    festival_price, festival_percent, festival_reason = apply_festival_discount(base_price, event)

    # Step 2: Weekend
    weekend_price, weekend_percent, weekend_reason = apply_weekend_discount(festival_price)

    # Step 3: Long-Stay
    longstay_price, longstay_percent, longstay_reason = apply_longstay_discount(weekend_price, days)

    # Combine results
    final_price = longstay_price
    total_discount_amount = base_price - final_price
    total_discount_percent = ((total_discount_amount / base_price) * 100) if base_price > 0 else D(0)

    # Combine reasons
    reasons = [r for r in [festival_reason, weekend_reason, longstay_reason] if r]
    discount_reason = " + ".join(reasons) if reasons else None

    return {
        "final_price": float(round(final_price, 2)),
        "total_discount_percent": float(round(total_discount_percent, 1)),
        "total_discount_amount": float(round(total_discount_amount, 2)),
        "discount_reason": discount_reason
    }
