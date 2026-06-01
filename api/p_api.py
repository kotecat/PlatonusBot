import httpx
from typing import Optional, Literal
from config import app_config
from api.cache import cache, CacheType
from schemas.journal import Journal, JournalMarks
from schemas.terms import (
    CurrentTerm, CurrentYear,
    Terms, Years, StudyRoomsYears
)
from schemas.university import UniversityItem
from schemas.college import RegionItem, CollegeItem


LanguageType = Literal["ru", "kz", "en"]


def language_to_num(lang: LanguageType) -> int:
    mapping = {"ru": 1, "kz": 2, "en": 3}
    return mapping.get(lang, 1)


class PlatonusApi:

    def __init__(self, host: str, login: str, password: str, language: str = "ru"):
        """
        :param host: домен университета, например 'plt.keu.kz'
        """
        self.base_url = f"https://{host}/rest"
        self.host = host
        self.login = login
        self.password = password
        self.language = language
        self.auth_token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def language_num(self) -> int:
        return language_to_num(self.language)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30)
        return self._client

    # ---------- Auth ----------

    async def authenticate(self) -> dict:
        client = await self._get_client()
        url = f"{self.base_url}/api/mobile/authentication/login"
        params = {"language": self.language_num, "lang": self.language_num}
        payload = {
            "login": self.login,
            "iin": "",
            "icNumber": "",
            "password": self.password,
        }
        response = await client.post(url, params=params, json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get("login_status") != "success":
            raise ValueError(f"Авторизация не удалась: {data}")

        self.auth_token = data["auth_token"]
        return data

    async def _ensure_auth(self):
        if not self.auth_token:
            await self.authenticate()

    async def _get(self, path: str, params: Optional[dict] = None) -> dict:
        await self._ensure_auth()
        client = await self._get_client()
        url = f"{self.base_url}{path}"
        headers = {"Token": self.auth_token}
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    async def _post(self, path: str, payload: dict, params: Optional[dict] = None) -> dict:
        await self._ensure_auth()
        client = await self._get_client()
        url = f"{self.base_url}{path}"
        headers = {"Token": self.auth_token}
        response = await client.post(url, headers=headers, json=payload, params=params)
        response.raise_for_status()
        return response.json()

    # ---------- Methods ----------

    @cache(CacheType.LOGIN, ttl=3)
    async def get_journal(self, year: int, semester: int) -> list[Journal]:
        path = f"/api/journal/{year}/{semester}/{self.language}"
        data = await self._get(path, params={"lang": self.language_num})
        return [Journal.model_validate(item) for item in data]

    @cache(CacheType.LOGIN, ttl=60)
    async def get_journal_marks(self, subject_id: int, study_year: int, term: int) -> dict:
        path = f"/mobile/journalMarks/{subject_id}"
        data = await self._post(
            path,
            payload={"studyYear": study_year, "term": term},
            params={"lang": self.language_num}
        )
        return data
    
    @cache(CacheType.UNIVERSITY, ttl=300)
    async def get_main_menu(self) -> dict:
        path = "/mobile/mainMenu/get"
        return await self._get(path, params={"lang": self.language})

    @cache(CacheType.LOGIN, ttl=30)
    async def get_journal_years(self) -> Years:
        path = "/mobile/years"
        data = await self._get(path, params={"lang": self.language_num, "forStudyRooms": False})
        return Years.model_validate(data)
    
    @cache(CacheType.LOGIN, ttl=30)
    async def get_study_rooms_years(self) -> StudyRoomsYears:
        path = "/mobile/years"
        data = await self._get(path, params={"lang": self.language_num, "forStudyRooms": True})
        return StudyRoomsYears.model_validate(data)
    
    @cache(CacheType.LOGIN, ttl=30)
    async def get_journal_semesters(self) -> Terms:
        path = "/mobile/terms"
        data = await self._get(path, params={"lang": self.language_num})
        return Terms.model_validate(data)

    @cache(CacheType.UNIVERSITY, ttl=300)
    async def get_current_year(self) -> CurrentYear:
        path = "/common/currentStudyYear"
        data = await self._get(path, params={"lang": self.language_num})
        return CurrentYear.model_validate(data)

    @cache(CacheType.UNIVERSITY, ttl=300)
    async def get_current_semester(self) -> CurrentTerm:
        path = "/universitySettings/default_term"
        data = await self._get(path, params={"lang": self.language_num})
        return CurrentTerm.model_validate(data)
    
    @cache(CacheType.LOGIN, ttl=60)
    async def get_user_info(self) -> dict:
        path = f"/mobile/personInfo/{self.language}"
        data = await self._get(path, params={"lang": self.language_num})
        return data

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


# ---------- Без авторизации ----------

async def get_universities() -> list[UniversityItem]:
    """
    Список всех университетов Платонуса.
    Каждый объект содержит: id, nameRu, nameKz, nameEn, protocol, url, port, context
    """
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(app_config.BASE_URL)
        data = response.raise_for_status().json()
        return [UniversityItem.model_validate(item) for item in data]


async def get_regions_college():
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"https://m.platonus.kz/pms/api/mobile/university/mobileAccessCollegeRegions"
        response = await client.get(url)
        data = response.raise_for_status().json()
        return [RegionItem.model_validate(item) for item in data]


async def get_colleges_by_region(region_id: int):
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"https://dev-m.platonus.kz/pms/api/mobile/university/mobileAccessCollegeByRegion/{region_id}"
        response = await client.get(url)
        data = response.raise_for_status().json()
        return [CollegeItem.model_validate(item) for item in data]
