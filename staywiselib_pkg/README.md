# staywiselib-shridharan

This is a custom Python library used in the StayWise project.
It calculates discounts based on festival, weekend, and long-stay pricing.

## Example
```python
from staywiselib.pricing import apply_festival_discount

price, discount, reason = apply_festival_discount(1000, event="Diwali")
print(price, discount, reason)
