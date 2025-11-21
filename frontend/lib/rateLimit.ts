/**
 * Simple Token Bucket Rate Limiter
 * 
 * @param {number} limit - Maximum number of requests allowed within the window
 * @param {number} windowMs - Time window in milliseconds
 * @returns {Object} - Rate limiter instance with check() method
 */
interface RateLimiter {
  check: (ip: string) => boolean;
}

export function rateLimit(limit: number, windowMs: number): RateLimiter {
  const hits = new Map<string, number>();
  const lastReset = new Map<string, number>();

  return {
    check: (ip: string) => {
      const now = Date.now();
      const resetTime = lastReset.get(ip) || 0;

      if (now - resetTime > windowMs) {
        hits.set(ip, 0);
        lastReset.set(ip, now);
      }

      const count = hits.get(ip) || 0;
      if (count >= limit) {
        return false;
      }
      hits.set(ip, count + 1);
      return true;
    },
  };
};
