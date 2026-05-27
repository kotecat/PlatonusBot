import httpx
from typing import Optional
from config import app_config
from api.cache import cache, CacheType


class PlatonusApi:

    def __init__(self, host: str, login: str, password: str, language: int = 1):
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

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30)
        return self._client

    # ---------- Auth ----------

    async def authenticate(self) -> dict:
        client = await self._get_client()
        url = f"{self.base_url}/api/mobile/authentication/login"
        params = {"language": self.language, "lang": self.language}
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
    async def get_journal(self, year: int, semester: int, lang: str = "ru") -> dict:
        path = f"/api/journal/{year}/{semester}/{lang}"
        return await self._get(path, params={"lang": lang})

    @cache(CacheType.UNIVERSITY, ttl=300)
    async def get_main_menu(self, lang: str = "ru") -> dict:
        path = "/mobile/mainMenu/get"
        return await self._get(path, params={"lang": lang})

    @cache(CacheType.LOGIN, ttl=30)
    async def get_journal_years(self, lang: int = 1, for_study_rooms: bool = False) -> dict:
        path = "/mobile/years"
        return await self._get(path, params={"lang": lang, "forStudyRooms": for_study_rooms})

    @cache(CacheType.LOGIN, ttl=30)
    async def get_journal_semesters(self, lang: int = 1) -> dict:
        path = "/mobile/terms"
        return await self._get(path, params={"lang": lang})

    @cache(CacheType.UNIVERSITY, ttl=300)
    async def get_current_year(self, lang: int = 1) -> dict:
        path = "/common/currentStudyYear"
        return await self._get(path, params={"lang": lang})

    @cache(CacheType.UNIVERSITY, ttl=300)
    async def get_current_semester(self, lang: int = 1) -> dict:
        path = "/universitySettings/default_term"
        return await self._get(path, params={"lang": lang})

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


# ---------- Без авторизации ----------

async def get_universities() -> list[dict]:
    """
    Список всех университетов Платонуса.
    Каждый объект содержит: id, nameRu, nameKz, nameEn, protocol, url, port, context
    """
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(app_config.BASE_URL)
        response.raise_for_status()
        return response.json()
