// Unit tests for map.config.ts: the checks that catch a mistyped config, and the privacy floor
// on the location blur. Run: pnpm test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { site, organizer, privacy, links, textTokens, blurMiles, configIssues } from '../map.config.ts';

test('the shipped config has no problems', () => {
  assert.deepEqual(configIssues(), []);
});

test('Title-case tokens capitalize each word, including after a hyphen', () => {
  assert.equal(textTokens.Toy, 'Yo-Yo');
  assert.equal(textTokens.Toys, 'Yo-Yos');
  assert.equal(textTokens.Players, 'Players');
});

test('the blur never goes below the privacy minimum', () => {
  const saved = privacy.blurMiles;
  try {
    privacy.blurMiles = 1;
    assert.equal(blurMiles(), privacy.minBlurMiles);
    assert.ok(configIssues().some((m) => /blurMiles/.test(m)));
    privacy.blurMiles = Number.NaN;
    assert.equal(blurMiles(), privacy.minBlurMiles);
    privacy.blurMiles = 25;
    assert.equal(blurMiles(), 25);
    assert.deepEqual(configIssues(), []);
  } finally {
    privacy.blurMiles = saved;
  }
});

test('mistakes in the config are reported', () => {
  const saved = { url: site.url, email: organizer.contactEmail, ig: organizer.instagram, center: site.mapView.center, link: links.topbar[0].href };
  try {
    site.url = 'example.org';
    organizer.contactEmail = 'not-an-email';
    organizer.instagram = '@club';
    site.mapView.center = [123, 0];
    links.topbar[0].href = 'example.org';
    const issues = configIssues().join(' | ');
    assert.match(issues, /site\.url/);
    assert.match(issues, /contactEmail/);
    assert.match(issues, /instagram/);
    assert.match(issues, /mapView\.center/);
    assert.match(issues, /must start with http/);
  } finally {
    site.url = saved.url;
    organizer.contactEmail = saved.email;
    organizer.instagram = saved.ig;
    site.mapView.center = saved.center;
    links.topbar[0].href = saved.link;
  }
  assert.deepEqual(configIssues(), []);
});
