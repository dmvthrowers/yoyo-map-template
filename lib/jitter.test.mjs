// Unit tests for the location blur. Run: pnpm test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { jitterPoint } from './jitter.ts';

function miles(a, b) {
  const R = 3958.8, rad = (d) => (d * Math.PI) / 180;
  const h = Math.sin(rad(b.lat - a.lat) / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(rad(b.lng - a.lng) / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

test('a blurred point is never farther than the radius from the original, at any latitude', () => {
  for (const [lat, lng, radius] of [[38.9, -77.0, 10], [0, 0, 5], [64.1, -21.9, 10], [-33.9, 151.2, 25]]) {
    for (let i = 0; i < 2000; i++) {
      const p = jitterPoint(lat, lng, radius);
      assert.ok(miles({ lat, lng }, p) <= radius * 1.01, `${lat},${lng} r=${radius}`);
    }
  }
});

test('the blur really moves the point and fills the disk (not one spot, not just the edge)', () => {
  const dists = Array.from({ length: 4000 }, () => miles({ lat: 40, lng: -100 }, jitterPoint(40, -100, 10)));
  const mean = dists.reduce((a, b) => a + b, 0) / dists.length;
  assert.ok(mean > 5.5 && mean < 7.8, `mean distance ${mean}`); // uniform over a disk of radius r has mean 2r/3
  assert.ok(dists.filter((d) => d < 1).length > 10);
  assert.ok(dists.filter((d) => d > 9).length > 100);
});

test('the same random numbers give the same point (the blur is pure given its randomness)', () => {
  const seq = () => { let i = 0; const v = [0.25, 0.75]; return () => v[i++ % 2]; };
  assert.deepEqual(jitterPoint(10, 20, 10, seq()), jitterPoint(10, 20, 10, seq()));
});
