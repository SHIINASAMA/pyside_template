import os
import platform
from urllib.parse import urlparse

from glom import glom
from httpx import AsyncClient

from .update import Updater, Version


class GitlabUpdater(Updater):
    base_url: str = "https://gitlab.com"
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
        return GitlabUpdater._instance

    def create_async_client(self) -> AsyncClient:
        if not self._headers:
            headers = {}
            if self.token:
                headers["PRIVATE-TOKEN"] = self.token
            self._headers = headers
        return AsyncClient(proxy=self.proxy, headers=self._headers, timeout=self.timeout)

    async def fetch(self):
        async with self.create_async_client() as client:
            r = await client.get(
                url=f"{self.base_url}/api/v4/projects",
                params={"search": self.project_name,
                        "search_namespaces": "true"},
            )
            r.raise_for_status()
            projects = r.json()
            if not projects:
                raise FileNotFoundError(f"Project {self.project_name} not found on GitLab: {self.base_url}")
            project = projects[0]
            project_id = project['id']
            r = await client.get(
                url=f"{self.base_url}/api/v4/projects/{project_id}/releases",
                params={"per_page": 1},
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
            self.description = latest_release['description']

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
            package_name = f"App-{sysname}-{arch}"

            self.download_url = None
            for link in glom(latest_release, 'assets.links', default={}):
                if package_name in link['name']:
                    self.download_url = link['url']
                    break
            if self.download_url is None:
                raise FileNotFoundError(f"Package {package_name} not found in release assets.")

            r = await client.head(url=self.download_url)
            r.raise_for_status()

            path = urlparse(self.download_url).path
            self.filename = os.path.basename(path)
