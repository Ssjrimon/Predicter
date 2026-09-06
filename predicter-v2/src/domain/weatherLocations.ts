/**
 * The handoff verified historical base-rate results for three cities'
 * high-temperature markets (Part IV, Part VI): New York (`KXHIGHNY`,
 * ticker format confirmed), Miami, and Austin (mentioned by name, exact
 * ticker prefixes not given). Rather than guess at those two cities'
 * ticker prefixes, this feature takes an explicit city selection instead
 * of inferring location from the ticker string.
 *
 * Coordinates and timezones are well-known, stable geographic facts, not
 * the kind of claim this project's discipline exists to verify against a
 * live API — unlike a JSON wire format, a city's approximate lat/long
 * does not need independent confirmation.
 */
export interface WeatherLocation {
  readonly name: string;
  readonly latitude: number;
  readonly longitude: number;
  readonly timezone: string;
}

export const KNOWN_WEATHER_LOCATIONS = {
  'New York, NY': { name: 'New York, NY', latitude: 40.7128, longitude: -74.006, timezone: 'America/New_York' },
  'Miami, FL': { name: 'Miami, FL', latitude: 25.7617, longitude: -80.1918, timezone: 'America/New_York' },
  'Austin, TX': { name: 'Austin, TX', latitude: 30.2672, longitude: -97.7431, timezone: 'America/Chicago' },
} satisfies Record<string, WeatherLocation>;

export type WeatherLocationName = keyof typeof KNOWN_WEATHER_LOCATIONS;
