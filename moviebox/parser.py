from moviebox.client import MovieBoxClient
from moviebox.models import (
    DownloadableFilesModel,
    SearchResultsModel,
    SubjectModel,
)


class MovieBoxParser:
    def __init__(self, client: MovieBoxClient):
        self.client = client

    async def search(self, query: str, is_movie: bool, page: int = 1, per_page: int = 10) -> SearchResultsModel:
        subject_type = 1 if is_movie else 2
        payload = {
            "keyword": query,
            "page": page,
            "perPage": per_page,
            "subjectType": subject_type,
            "tabId": "All"
        }
        
        try:
            data = await self.client.post("/wefeed-mobile-bff/subject-api/search/v2", payload)
            
            results = data.get("results", [])
            items = []
            if results:
                subjects = results[0].get("subjects", [])
                for sub in subjects:
                    if sub.get("subjectType") == subject_type:
                        items.append(sub)
            
            data["items"] = items
            return SearchResultsModel.model_validate(data)
        except Exception:
            payload.pop("tabId", None)
            data = await self.client.post("/wefeed-mobile-bff/subject-api/search", payload)
            
            items = []
            for sub in data.get("items", []):
                if sub.get("subjectType") == subject_type:
                    items.append(sub)
            
            data["items"] = items
            return SearchResultsModel.model_validate(data)

    async def get_download_links(self, subject_id: str, resolution: str, is_movie: bool, season: int = 1, episode: int = 1, page: int = 1, per_page: int = 20) -> DownloadableFilesModel:
        path = f"/wefeed-mobile-bff/subject-api/resource?subjectId={subject_id}&resolution={resolution}&page={page}&perPage={per_page}"
        
        if not is_movie:
            path += f"&se={season}&epFrom={episode}&epTo={episode}&all=0&pagerMode=0"
            
        data = await self.client.get(path)
        return DownloadableFilesModel.model_validate(data)
