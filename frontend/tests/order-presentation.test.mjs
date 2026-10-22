import test from 'node:test';
import assert from 'node:assert/strict';
import { orderDate, orderFulfillmentStep, orderStatusLabel, orderToman } from '../src/lib/order-presentation.ts';

test('order states are distinct and never imply payment before verification', () => {
  assert.equal(orderStatusLabel('pending_payment'), 'در انتظار پرداخت');
  assert.equal(orderStatusLabel('paid'), 'پرداخت‌شده');
  assert.equal(orderStatusLabel('processing'), 'در حال آماده‌سازی');
  assert.equal(orderStatusLabel('shipped'), 'ارسال‌شده');
  assert.equal(orderStatusLabel('delivered'), 'تحویل‌شده');
  assert.equal(orderStatusLabel('cancelled'), 'لغوشده');
  assert.equal(orderStatusLabel('expired'), 'منقضی‌شده');
});

test('Rial order prices are displayed as Toman exactly once', () => {
  assert.equal(orderToman(250000000), '۲۵٬۰۰۰٬۰۰۰ تومان');
  assert.equal(orderToman(0), '۰ تومان');
});

test('malformed order date produces a safe human label', () => {
  assert.equal(orderDate('not-a-date'), 'تاریخ نامشخص');
});


test('fulfillment timeline never displays unpaid or cancelled orders as shipped', () => {
  assert.equal(orderFulfillmentStep('pending_payment'), 0);
  assert.equal(orderFulfillmentStep('cancelled'), 0);
  assert.equal(orderFulfillmentStep('expired'), 0);
  assert.equal(orderFulfillmentStep('paid'), 1);
  assert.equal(orderFulfillmentStep('processing'), 2);
  assert.equal(orderFulfillmentStep('shipped'), 3);
  assert.equal(orderFulfillmentStep('delivered'), 4);
});
