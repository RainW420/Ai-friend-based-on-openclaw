import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from restore_runtime_bundle import restore_bundle


class RestoreRuntimeBundleTests(unittest.TestCase):
    def test_restore_bundle_validates_required_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "bundle.tar.gz"
            manifest = {
                "format": "clawbot-cloud-readiness-v1",
                "files": [{"path": "config/example.json"}],
            }
            with tarfile.open(bundle, "w:gz") as tar:
                data = json.dumps(manifest).encode("utf-8")
                info = tarfile.TarInfo("clawbot-runtime/MANIFEST.json")
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
                for dirname in ["config", "workspace", "plugins/clawbot-readonly"]:
                    info = tarfile.TarInfo(f"clawbot-runtime/{dirname}")
                    info.type = tarfile.DIRTYPE
                    tar.addfile(info)
            result = restore_bundle(bundle, root / "restore")
            self.assertTrue(result["ok"])
            self.assertEqual(result["manifest_format"], "clawbot-cloud-readiness-v1")


if __name__ == "__main__":
    unittest.main()
