import platform

from glom import glom
from httpx import AsyncClient

from .update import Updater, Version


class GithubUpdater(Updater):
    base_url: str = "https://api.github.com"
    project_name: str = ""
    timeout = 5
    token = None

    _headers = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @staticmethod
    def instance():
        return GithubUpdater._instance

    def create_async_client(self) -> AsyncClient:
        if not self._headers:
            headers = {
                "Accept": "application/vnd.github+json"
            }
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            self._headers = headers
        return AsyncClient(proxy=self.proxy, headers=self._headers, timeout=self.timeout)

    async def fetch(self):
        async with self.create_async_client() as client:
            r = await client.get(
                url=f"{self.base_url}/repos/{self.project_name}/releases",
                params={
                    "pre_page": "100",
                    "page": "1"
                }
            )
            r.raise_for_status()
            releases = []
            for release in r.json():
                version = Version(release['tag_name'])
                if version.release_type == self.release_type:
                    releases.append(release)
            latest_release = max(releases, key=lambda x: Version(x['tag_name']), default=None)
            if latest_release is None:
                # Does have any release for this channel
                self.remote_version = Version('0.0.0.0')
                return
            self.remote_version = Version(latest_release['tag_name'])
            self.description = latest_release['body']

            arch = platform.machine().lower()
            if arch in ['x86_64', 'amd64']:
                arch = 'x64'
            elif arch in ['aarch64', 'arm64']:
                arch = 'arm64'
            else:
                raise RuntimeError(f"Unknown architecture: {arch}")

            sysname = platform.system().lower()
            if sysname == 'windows':
                sysname = 'windows'
            elif sysname == 'darwin':
                sysname = 'macos'
            elif sysname == 'linux':
                sysname = 'linux'
            else:
                raise RuntimeError(f"Unknown system: {sysname}")
            package_name = f"App-{sysname}-{arch}.zip"

            self.download_url = None
            for assets in glom(latest_release, 'assets', default={}):
                if assets['name'] == package_name:
                    self.download_url = assets['browser_download_url']

            if self.download_url is None:
                raise FileNotFoundError(f"Package {package_name} not found in release assets.")

            r = await client.head(url=self.download_url)
            r.raise_for_status()

            self.filename = package_name
