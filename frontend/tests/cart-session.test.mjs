import test from "node:test";
import assert from "node:assert/strict";

import {
  cartSessionIdentity,
  resolveCartForSession,
  shouldDiscardCartToken,
} from "../src/lib/cart-session.ts";

const accountCart = { token: "account-cart", items: [] };
const guestCart = { token: "guest-cart", items: [] };

function apiWithCalls({ getResult = guestCart, getError } = {}) {
  const calls = [];
  return {
    calls,
    getCart: async (token) => {
      calls.push(`get:${token}`);
      if (getError) throw getError;
      return getResult;
    },
    createCart: async () => {
      calls.push("create");
      return accountCart;
    },
    isNotFound: (error) => error?.status === 404,
  };
}

test("guest without a cart does not allocate an empty cart", async () => {
  const api = apiWithCalls();
  assert.equal(await resolveCartForSession(null, false, api), null);
  assert.deepEqual(api.calls, []);
});

test("authenticated session without local token restores server account cart", async () => {
  const api = apiWithCalls();
  assert.equal(await resolveCartForSession(null, true, api), accountCart);
  assert.deepEqual(api.calls, ["create"]);
});

test("guest token survives OTP login and is claimed via authenticated GET", async () => {
  const api = apiWithCalls();
  assert.equal(await resolveCartForSession("guest-token", true, api), guestCart);
  assert.deepEqual(api.calls, ["get:guest-token"]);
});

test("guest reload reuses existing guest cart", async () => {
  const api = apiWithCalls();
  assert.equal(await resolveCartForSession("guest-token", false, api), guestCart);
  assert.deepEqual(api.calls, ["get:guest-token"]);
});

test("invalid token recovers account cart after a 404", async () => {
  const api = apiWithCalls({ getError: { status: 404 } });
  assert.equal(await resolveCartForSession("expired", true, api), accountCart);
  assert.deepEqual(api.calls, ["get:expired", "create"]);
});

test("invalid guest token is discarded instead of creating a cart", async () => {
  const api = apiWithCalls({ getError: { status: 404 } });
  assert.equal(await resolveCartForSession("expired", false, api), null);
  assert.deepEqual(api.calls, ["get:expired"]);
});

test("network failures propagate instead of being mistaken for empty carts", async () => {
  const failure = new Error("connection refused");
  const api = apiWithCalls({ getError: failure });
  await assert.rejects(resolveCartForSession("saved", true, api), failure);
  assert.deepEqual(api.calls, ["get:saved"]);
});

test("account token clears on logout or user switch, but guest token survives login", () => {
  assert.equal(cartSessionIdentity(null), "guest");
  assert.equal(cartSessionIdentity(42), "user:42");
  assert.equal(shouldDiscardCartToken("guest", "user:42"), false);
  assert.equal(shouldDiscardCartToken("user:42", "guest"), true);
  assert.equal(shouldDiscardCartToken("user:42", "user:7"), true);
  assert.equal(shouldDiscardCartToken("user:42", "user:42"), false);
  assert.equal(shouldDiscardCartToken(null, "user:42"), false);
});
