import importlib.util
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SPEC = importlib.util.spec_from_file_location(
    "airspace_update", Path(__file__).parents[1] / "scripts" / "update.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WeatherClassificationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 11, 8, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    def classify(self, text):
        return MODULE.classify_weather_sources([
            {"name": "中央气象台", "url": "https://www.nmc.cn/example", "text": text}
        ], self.now)

    def test_tropical_disturbance_affecting_hainan_is_watch(self):
        result = self.classify(
            "未来三天，南海有一个热带扰动活动，它将给海南岛带来大到暴雨天气，海域阵风8级。"
        )
        self.assertEqual(result["status"], "watch")
        self.assertEqual(result["stage"], "disturbance")
        self.assertTrue(result["affects_hainan"])
        self.assertFalse(result["named"])
        self.assertIn("大到暴雨", result["hazards"])
        self.assertIn("海上大风", result["hazards"])

    def test_named_typhoon_is_active(self):
        result = self.classify("今年第25号台风“杜鹃”预计移向海南岛，并带来暴雨。")
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["stage"], "named")
        self.assertTrue(result["named"])

    def test_unrelated_weather_stays_none(self):
        result = self.classify("海南岛今天多云，局地有普通雷阵雨。")
        self.assertEqual(result["status"], "none")
        self.assertFalse(result["affects_hainan"])


if __name__ == "__main__":
    unittest.main()
