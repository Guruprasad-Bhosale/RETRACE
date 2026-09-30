"""Route Tracking Module."""

from apps.worker.exploration.state_identity import StateIdentityCalculator


class RouteTracker:
    """Tracks unique origin-relative routes reached during exploration."""

    def __init__(self) -> None:
        self._visited_routes: set[str] = set()

    def record_url(self, url: str) -> str:
        """Normalize URL and record route."""
        route = StateIdentityCalculator.normalize_route(url)
        self._visited_routes.add(route)
        return route

    def get_routes(self) -> list[str]:
        """Return sorted list of discovered routes."""
        return sorted(self._visited_routes)

    def count(self) -> int:
        return len(self._visited_routes)
