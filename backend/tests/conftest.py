import os
import sys
from dotenv import load_dotenv

tests_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(tests_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

load_dotenv(os.path.join(backend_dir, ".env"))

# Provide graceful mocks for optional geoalchemy2 types if geoalchemy2 package is not installed in local environment
try:
    import geoalchemy2
except ImportError:
    from unittest.mock import MagicMock
    from sqlalchemy.types import UserDefinedType

    class MockGeometry(UserDefinedType):
        cache_ok = True
        def __init__(self, *args, **kwargs):
            pass
        def get_col_spec(self, **kw):
            return "GEOMETRY"

    mock_geo = MagicMock()
    mock_geo.Geometry = MockGeometry
    mock_geo.Geography = MockGeometry
    sys.modules['geoalchemy2'] = mock_geo
