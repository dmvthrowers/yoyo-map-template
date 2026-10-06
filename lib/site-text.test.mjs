// Unit tests for {{token}} filling and for the shipped messages. Run: pnpm test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fillTokens, fillMessages, unknownTokens } from './site-text.ts';
import { textTokens } from '../map.config.ts';

const en = JSON.parse(readFileSync(new URL('../messages/en.json', import.meta.url), 'utf8'));

test('fillTokens replaces known tokens and keeps unknown ones visible', () => {
  assert.equal(fillTokens('Find {{toys}} {{players}}', { toys: 'kendamas', players: 'players' }), 'Find kendamas players');
  assert.equal(fillTokens('Hi {{ name }}!', { name: 'Sam' }), 'Hi Sam!');
  assert.equal(fillTokens('Oops {{nope}}', { toys: 'x' }), 'Oops {{nope}}');
  assert.equal(fillTokens('no tokens {count}', {}), 'no tokens {count}');
});

test('fillMessages fills every string in a nested object and leaves ICU placeholders alone', () => {
  const out = fillMessages({ a: { b: '{{Toy}} in {city}', c: ['{{toy}}', 3] }, n: '{count, plural, one {# {{player}}} other {# {{players}}}}' },
    { Toy: 'Kendama', toy: 'kendama', player: 'player', players: 'players' });
  assert.equal(out.a.b, 'Kendama in {city}');
  assert.deepEqual(out.a.c, ['kendama', 3]);
  assert.equal(out.n, '{count, plural, one {# player} other {# players}}');
});

test('unknownTokens lists tokens with no value', () => {
  assert.deepEqual(unknownTokens({ a: '{{toy}} {{bogus}}', b: ['{{alsoBogus}}'] }, { toy: 'x' }), ['alsoBogus', 'bogus']);
});

test('every {{token}} used in messages/en.json has a value in map.config.ts', () => {
  assert.deepEqual(unknownTokens(en, textTokens), []);
});

test('the shipped messages carry no club-specific wording', () => {
  const text = JSON.stringify(en);
  assert.doesNotMatch(text, /dmvthrowers|DMV Throwers|VSYC|yoyoarchive|ko-fi/i);
  // The toy comes from the config, not the words.
  assert.doesNotMatch(text.replace(/"skill_toy[^"]*"/g, ''), /yo-?yo/i);
});

test('filled English messages read naturally with the default config', () => {
  const filled = fillMessages(en, textTokens);
  assert.match(filled.map.pageTitle, /^Yo-Yo Player Map — Find Players, Shops & Clubs Near You$/);
  assert.match(filled.home.mapWorks.items[0].body, /up to 10 miles/);
  assert.doesNotMatch(JSON.stringify(filled), /\{\{/);
});

test('a kendama config fills the same messages', () => {
  const tokens = { ...textTokens, toy: 'kendama', toys: 'kendamas', Toy: 'Kendama', Toys: 'Kendamas', player: 'tamer', players: 'tamers', Player: 'Tamer', Players: 'Tamers' };
  const filled = fillMessages(en, tokens);
  assert.equal(filled.map.pageTitle, 'Kendama Tamer Map — Find Tamers, Shops & Clubs Near You');
  assert.equal(filled.players.throwerCount, '{count, plural, one {# tamer} other {# tamers}}');
});
