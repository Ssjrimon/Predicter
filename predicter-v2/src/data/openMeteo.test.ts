import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchDailyMaxTempsForCalendarDay } from './openMeteo';
import { KNOWN_WEATHER_LOCATIONS } from '../domain/weatherLocations';

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), { status: 200, headers: { 'content-type': 'application/json' } });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('fetchDailyMaxTempsForCalendarDay', () => {
  it('filters a multi-year daily response down to the matching calendar day', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse({
          daily: {
            time: ['2020-01-01', '2020-01-02', '2021-01-01', '2021-06-15', '2022-01-01'],
            temperature_2m_max: [58, 70, 62, 90, 61],
          },
        }),
      ),
    );

    const temps = await fetchDailyMaxTempsForCalendarDay(
      KNOWN_WEATHER_LOCATIONS['New York, NY'],
      1,
      1,
      2022,
      3,
    );

    expect(temps).toEqual([58, 62, 61]);
  });

  it('requests one single-range query, not one request per year', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ daily: { time: [], temperature_2m_max: [] } }));
    vi.stubGlobal('fetch', fetchMock);

    await fetchDailyMaxTempsForCalendarDay(KNOWN_WEATHER_LOCATIONS['New York, NY'], 1, 1, 2023, 10);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const url = fetchMock.mock.calls[0]?.[0] as string;
    expect(url).toContain('start_date=2014-01-01');
    expect(url).toContain('end_date=2023-12-31');
    expect(url).toContain('temperature_unit=fahrenheit');
  });

  it('skips null readings rather than treating them as 0 degrees', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse({ daily: { time: ['2020-01-01', '2021-01-01'], temperature_2m_max: [null, 55] } }),
      ),
    );

    const temps = await fetchDailyMaxTempsForCalendarDay(KNOWN_WEATHER_LOCATIONS['New York, NY'], 1, 1, 2021, 2);
    expect(temps).toEqual([55]);
  });

  it('returns null when the underlying request fails, via the defensive fetch pattern', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('err', { status: 500 })));
    const temps = await fetchDailyMaxTempsForCalendarDay(KNOWN_WEATHER_LOCATIONS['New York, NY'], 1, 1, 2023, 10);
    expect(temps).toBeNull();
  });
});
