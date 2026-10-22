# ELASI shipping pricing — merchant sign-off needed

The customer-facing checkout uses exactly one server-side flat postal fee.
The merchant must first **approve** the amount and that a single rate applies
throughout Iran; no assumption about free shipping is permitted.

1. Configure the Django environment `ELASI_POSTAL_SHIPPING_FEE_RIAL` as a
   **nonnegative integer in Rial, divisible by 10**; only use `0` when free shipping is approved.
2. When unset/negative, `/api/v1/checkout/shipping-quote/` returns 503
   (`shipping_fee_unconfigured`) and creating orders via `/api/v1/checkout/`
   also returns 503; no order or stock reservation is created.
3. The frontend must fetch the server quote before allowing submission. The
   checkout service reads the setting again at order creation; the stored
   order total remains authoritative even if rates change between quote and
   submission. Never trust a client-submitted fee.
4. If shipping requires different rates by province, weight, city or order
   value, do **not** configure the flat fee. Implement and test a location-
   aware server quote with merchant-signed rules first.
5. Payment providers are not yet active. A created order is pending payment,
   not paid, and does not represent a completed sale.
