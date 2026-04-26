commit 2ba8914153cdd54d6613e2eca0b1ef79be2443f3
Author: Dev User <dev@example.com>
Date:   2026-04-26 14:21

    Fix MAX_DISCOUNT_PERCENT cap to 100
    
    A discount greater than 100% would result in negative prices,
    which is invalid business logic. Correct the cap from 150 to 100.

diff --git a/src/pricing/discount.py b/src/pricing/discount.py
index 7a64513..191aa3b 100644
--- a/src/pricing/discount.py
+++ b/src/pricing/discount.py
@@ -1,6 +1,6 @@
 """Discount calculation utilities."""
 
-MAX_DISCOUNT_PERCENT = 150
+MAX_DISCOUNT_PERCENT = 100
 
 
 def calculate_discount(price: float, discount_percent: float) -> float:
