import logging

import httpx

logger = logging.getLogger("uvicorn.error")


class WikiService:
    @staticmethod
    def _scale_wikimedia_url(url: str, width: int = 500) -> str:
        """
        Ensures the Wikimedia Commons URL points to a scaled thumbnail version
        instead of the raw full-resolution image.
        """
        if "upload.wikimedia.org" in url and "/thumb/" in url:
            parts = url.split("/")
            last_part = parts[-1]
            if "px-" in last_part:
                filename = last_part.split("px-", 1)[1]
                parts[-1] = f"{width}px-{filename}"
                return "/".join(parts)
        return url

    @staticmethod
    def _is_invalid_diagram(url: str) -> bool:
        """
        Checks if the URL points to a technical diagram, size comparison, or vector graphic
        instead of a real photograph.
        """
        lowered_url = url.lower()
        bad_keywords = ["diagram", "scale", "size", "comparison", ".svg"]
        return any(keyword in lowered_url for keyword in bad_keywords)

    @staticmethod
    async def get_species_image_url(species_name: str) -> str:
        """
        Fetches a web-friendly, real photograph URL for a given biological species
        using Wikipedia REST API endpoints, filtering out technical diagrams.
        """
        clean_name = " ".join(species_name.split())
        query_term = clean_name

        if "(" in clean_name and ")" in clean_name:
            query_term = clean_name.split("(")[1].split(")")[0]

        query_parts = query_term.strip().split()
        if len(query_parts) >= 2:
            genus = query_parts[0].capitalize()
            species_descriptor = query_parts[1].lower()
            query_term = f"{genus}_{species_descriptor}"
        else:
            query_term = query_term.capitalize()

        headers = {"User-Agent": "SharkTrackingGraphBot/1.0 (contact: admin@sharktrackinggraph.local)"}

        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query_term}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(summary_url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    raw_url = None

                    if "thumbnail" in data:
                        raw_url = data["thumbnail"]["source"]
                    elif "originalimage" in data:
                        raw_url = data["originalimage"]["source"]

                    if raw_url and not WikiService._is_invalid_diagram(raw_url):
                        return WikiService._scale_wikimedia_url(raw_url, width=500)
        except Exception as e:
            logger.error(f"Summary API failed for {query_term}: {e}")

        media_url = f"https://en.wikipedia.org/api/rest_v1/page/media-list/{query_term}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(media_url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    media_data = response.json()
                    items = media_data.get("items", [])

                    for item in items:
                        if item.get("type") == "image":
                            srcset = item.get("srcset", [])
                            if srcset:
                                candidate_url = "https:" + srcset[0]["src"]
                                if not WikiService._is_invalid_diagram(candidate_url):
                                    return WikiService._scale_wikimedia_url(candidate_url, width=500)
        except Exception as e:
            logger.error(f"Media list API failed for {query_term}: {e}")

        return "https://commons.wikimedia.org/wiki/File:No_image_available.svg"


if __name__ == "__main__":
    import asyncio

    # Array of target species extracted from data analysis
    TEST_SPECIES = [
        "Blacktip Shark (Carcharhinus limbatus)",
        "Blue Shark (Prionace glauca)",
        "Bull Shark (Carcharhinus leucas)",
        "Hammerhead Shark (Sphyrna)",
        "Mako Shark (Isurus oxyrinchus)",
        "Silky Shark (Carcharhinus falciformis)",
        "Tiger Shark  (Galeocerdo cuvier)",
        "Whale Shark (Rhincodon Typus)",
        "White Shark (Carcharodon carcharias)",
    ]

    async def run_test():
        print("=" * 90)
        print("LAUNCHING WIKIPEDIA REST API RESOLUTION TEST FOR SHARK SPECIES")
        print("=" * 90)

        for species in TEST_SPECIES:
            url = await WikiService.get_species_image_url(species)
            print(f"Species:    {species}")
            print(f"Result URL: {url}")
            print("-" * 90)

    asyncio.run(run_test())
