commit 38dbb699e3f2ccc91bcd7c63a03ce0b7bd7efe4e
Author: Dev User <dev@example.com>
Date:   2026-04-26 14:20

    Cap maximum discount at 100% to prevent invalid over-discounting

diff --git a/src/pricing/discount.py b/src/pricing/discount.py
index 7a64513..191aa3b 100644
--- a/src/pricing/discount.py
+++ b/src/pricing/discount.py
@@ -1,6 +1,6 @@
 """Discount calculation utilities."""
 
-MAX_DISCOUNT_PERCENT = 150
+MAX_DISCOUNT_PERCENT = 100
 
 
 def calculate_discount(price: float, discount_percent: float) -> float:
