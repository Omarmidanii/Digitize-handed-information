<?php


namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;

class CountRequests
{
    public function handle(Request $request, Closure $next)
    {
        // App-wide total counter (create if missing, keep 30 days)
        Cache::add('metrics:requests_total', 0, now()->addDays(30));
        Cache::increment('metrics:requests_total');

        // Per-day, per-route counter
        $route = $request->route();
        $name = $route?->getName() ?? $route?->uri() ?? 'unknown';
        if ($name != "ana")
            return 0;
        $key = 'metrics:route:' . $name . ':' . now()->toDateString();
        Cache::add($key, 0, now()->addDays(2)); // seed with TTL
        Cache::increment($key);

        return $next($request);
    }
}