/**
 * Moves a point to a uniformly random spot inside a circle of `miles` around it. Pure and
 * import-free so it can be unit tested; lib/geocode.ts passes the configured radius.
 */
export function jitterPoint(
  lat: number,
  lng: number,
  miles: number,
  random: () => number = Math.random,
): { lat: number; lng: number } {
  const r = (miles * Math.sqrt(random())) / 69; // uniform over the disk; one degree of latitude is ~69 miles
  const theta = 2 * Math.PI * random();
  const cosLat = Math.max(0.2, Math.cos((lat * Math.PI) / 180)); // clamp to avoid pole blowup
  return { lat: lat + r * Math.cos(theta), lng: lng + (r * Math.sin(theta)) / cosLat };
}
