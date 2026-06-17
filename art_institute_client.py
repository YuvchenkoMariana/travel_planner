from typing import Optional, Dict, Any
import requests


class APICache:
    """
    Simple in-memory cache for API responses.
    Useful for reducing duplicate API calls during testing.

    Note: TTL (time-to-live) functionality can be added if needed by storing
    timestamps with values and checking expiration in get().
    """

    def __init__(self):
        """Initialize the cache."""
        self._cache: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key (typically the full URL)

        Returns:
            Cached value if found, None otherwise
        """
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key (typically the full URL)
            value: Value to cache
        """
        self._cache[key] = value

    def clear(self) -> None:
        """Clear all cache entries. Useful for testing."""
        self._cache.clear()

    def size(self) -> int:
        """Get the number of entries in the cache."""
        return len(self._cache)


class ArtInstituteClient:
    """
    Client for interacting with the Art Institute of Chicago API.
    Includes response caching to minimize duplicate requests.
    """

    BASE_URL = "https://api.artic.edu/api/v1"

    def __init__(self, cache: Optional[APICache] = None):
        """
        Initialize the API client.

        Args:
            cache: Optional APICache instance. If None, creates a new cache.
        """
        self._cache = cache if cache is not None else APICache()

    def search_places(self, query: str, size: int = 10) -> Dict[str, Any]:
        """
        Search for places by name in the Art Institute API.

        Args:
            query: Search query (place name)
            size: Number of results to return (default: 10)

        Returns:
            JSON response from the API as a dictionary

        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.BASE_URL}/places/search"
        params = {"q": query, "size": size}

        # Create cache key from URL and params
        cache_key = f"{url}?q={query}&size={size}"

        # Check cache first
        cached_response = self._cache.get(cache_key)
        if cached_response is not None:
            return cached_response

        # Make API request
        response = requests.get(url, params=params)
        response.raise_for_status()

        json_data = response.json()

        # Cache the response
        self._cache.set(cache_key, json_data)

        return json_data

    def get_place_by_id(self, place_id: str) -> Dict[str, Any]:
        """
        Get a specific place by its ID.

        Args:
            place_id: The place ID

        Returns:
            JSON response from the API as a dictionary

        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.BASE_URL}/places/{place_id}"
        cache_key = url

        # Check cache first
        cached_response = self._cache.get(cache_key)
        if cached_response is not None:
            return cached_response

        # Make API request
        response = requests.get(url)
        response.raise_for_status()

        json_data = response.json()

        # Cache the response
        self._cache.set(cache_key, json_data)

        return json_data

    def find_place_by_name(self, place_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a place by name in the Art Institute API.
        Returns the first matching result.

        Args:
            place_name: Name of the place to search for

        Returns:
            Dictionary with 'id', 'title', 'api_link' keys if found, None otherwise
        """
        try:
            results = self.search_places(place_name)

            # Return first result if found
            if "data" in results and len(results["data"]) > 0:
                first_result = results["data"][0]
                return {
                    "id": str(first_result.get("id")),
                    "title": first_result.get("title", place_name),
                    "api_link": first_result.get("api_link", f"{self.BASE_URL}/places/{first_result.get('id')}")
                }

            return None

        except requests.RequestException:
            return None

    def validate_place(self, place_name: str, external_id: str) -> bool:
        """
        Validate that a place with the given name and external_id exists in the API.

        Args:
            place_name: Name of the place to search for
            external_id: Expected external ID from the API

        Returns:
            True if place exists and ID matches, False otherwise
        """
        try:
            results = self.search_places(place_name)

            # Check if any result matches the external_id
            if "data" in results:
                for place in results["data"]:
                    if str(place.get("id")) == str(external_id):
                        return True

            return False

        except requests.RequestException:
            return False

    def clear_cache(self) -> None:
        """Clear the API response cache. Useful for testing."""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """Get the number of cached responses."""
        return self._cache.size()


# Global instance for easy access
# Can be replaced with dependency injection in production
_default_client: Optional[ArtInstituteClient] = None


def get_client() -> ArtInstituteClient:
    """
    Get the default ArtInstituteClient instance.
    Creates one if it doesn't exist.

    Returns:
        ArtInstituteClient instance
    """
    global _default_client
    if _default_client is None:
        _default_client = ArtInstituteClient()
    return _default_client


def clear_cache() -> None:
    """Clear the cache of the default client."""
    client = get_client()
    client.clear_cache()
