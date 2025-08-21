from typing import List, Dict, Any, Optional
from ..http_client import SearchHTTPClient


def search_semantic_scholar(
    query: str,
    api_key: str,
    limit: int = 5,
    fields:
    str = "title,authors,year,abstract,url,venue,citationCount,externalIds,publicationDate",
) -> Optional[List[Dict[str, Any]]]:
    """
    Searches Semantic Scholar for a given query using an API key.

    Args:
        query: The search query string.
        api_key: Your Semantic Scholar API key.
        limit: The maximum number of results to return.
        fields: A comma-separated string of fields to retrieve for each paper.

    Returns:
        A list of dictionaries, where each dictionary represents a paper, or None if an error occurs.
    """

    base_url = "https://api.semanticscholar.org/graph/v1"
    endpoint = "/paper/search"
    url = f"{base_url}{endpoint}"

    # Set up the headers with your API key
    headers = {"x-api-key": api_key}

    # API request parameters
    params = {"query": query, "limit": limit, "fields": fields}

    print(f"Sending request to Semantic Scholar API: {query}...")

    try:
        # Create HTTP client with custom headers
        http_client = SearchHTTPClient(timeout=10.0, headers=headers)

        # Send GET request
        response = http_client.get(url, params=params)

        search_results = response.json()

        # Semantic Scholar API will return an empty "data" list when finding no results
        # or no 'data' key, so using get() is safer.
        return search_results.get("data", [])

    except Exception as e:
        print(f"An error occurred during the request: {e}")
        return None


def format_results(papers: List[Dict[str, Any]]) -> str:
    """
    Formats the search results into a readable string.
    """
    if not papers:
        return "No search results were found."

    try:
        docs = []
        for paper in papers:
            # Safely get all values
            title = paper.get("title", "N/A")
            # Authors are in a list and need to be processed
            authors = ", ".join([
                author["name"] for author in paper.get("authors", []) if author
            ])
            year = paper.get("year", "N/A")
            venue = paper.get("venue", "N/A")
            citation_count = paper.get("citationCount", 0)
            abstract = paper.get("abstract", "N/A")
            url = paper.get("url", "N/A")

            # **Improved and safer handling of external IDs**
            externalIds = paper.get(
                "externalIds")  # Returns the dictionary or None
            DOI = externalIds.get("DOI", "N/A") if externalIds else "N/A"
            PubMed = externalIds.get("PubMed", "N/A") if externalIds else "N/A"

            # Create the formatted string
            doc_string = (f"Title: {title}\n"
                          f"Authors: {authors}\n"
                          f"Journal: {venue}\n"
                          f"Year: {year} | Citations: {citation_count}\n"
                          f"DOI: {DOI} | PMID: {PubMed}\n"
                          f"URL: {url}\n"
                          f"Abstract: {abstract}\n")
            docs.append(doc_string)

        # Join all individual paper strings with two newlines
        return "\n\n".join(docs)

    except Exception as ex:
        return f"An exception occurred during result formatting: {ex}"


# --- Example Usage ---
if __name__ == "__main__":
    # Your API key
    MY_API_KEY = "XgYvPwQwoA7sGVwlSugMLngUe5gXjDF87X7ZpuOh"

    # The query you want to search for
    search_query = "Attention Is All You Need"

    # Call the search function with your query and API key
    papers_found = search_semantic_scholar(query=search_query,
                                           api_key=MY_API_KEY)

    # Format and print the results
    if papers_found is not None:
        formatted_output = format_results(papers_found)
        print(formatted_output)
