import { describe, expect, it } from 'vitest';
import { assignCategory } from './category';

describe('assignCategory', () => {
  it('detects KXFED as Fed', () => {
    expect(assignCategory('KXFED-25JUN-T5.25')).toEqual({ category: 'Fed', source: 'auto-detected' });
  });

  it('detects the verified KXHIGHNY ticker as Weather', () => {
    expect(assignCategory('KXHIGHNY-24JAN01-T60')).toEqual({ category: 'Weather', source: 'auto-detected' });
  });

  it('detects INX as Index', () => {
    expect(assignCategory('INX-SOMETHING')).toEqual({ category: 'Index', source: 'auto-detected' });
  });

  it('falls through to Other for an unrecognized prefix rather than guessing', () => {
    expect(assignCategory('RANDOMTICKER-1')).toEqual({ category: 'Other', source: 'auto-detected' });
  });

  it('is case-insensitive on the prefix', () => {
    expect(assignCategory('kxfed-x').category).toBe('Fed');
  });

  it('an explicit override always wins over auto-detection', () => {
    // Even a ticker that would auto-detect as Fed can be overridden.
    expect(assignCategory('KXFED-X', 'Weather')).toEqual({ category: 'Weather', source: 'user-override' });
  });
});
