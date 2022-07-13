# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import shutil
import unittest
import pytest

from threading import Event
from os import mkdir
from os.path import dirname, join, exists
from mock import Mock
from mock.mock import call
from mycroft_bus_client import Message
from ovos_utils.messagebus import FakeBus
from neon_utils.configuration_utils import get_neon_user_config

from mycroft.skills.skill_loader import SkillLoader


class TestSkill(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        bus = FakeBus()
        bus.run_in_thread()
        skill_loader = SkillLoader(bus, dirname(dirname(__file__)))
        skill_loader.load()
        cls.skill = skill_loader.instance

        # Define a directory to use for testing
        cls.test_fs = join(dirname(__file__), "skill_fs")
        if not exists(cls.test_fs):
            mkdir(cls.test_fs)

        # Override the fs paths to use the test directory
        cls.skill.settings_write_path = cls.test_fs
        cls.skill.file_system.path = cls.test_fs
        cls.skill._init_settings()
        cls.skill.initialize()

        # Override speak and speak_dialog to test passed arguments
        cls.skill.speak = Mock()
        cls.skill.speak_dialog = Mock()
        # TODO: Put any skill method overrides here

    def setUp(self):
        self.skill.speak.reset_mock()
        self.skill.speak_dialog.reset_mock()

        # TODO: Put any cleanup here that runs before each test case

    def tearDown(self) -> None:
        # TODO: Put any cleanup here that runs after each test case
        pass

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.test_fs)

    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills import NeonSkill

        self.assertIsInstance(self.skill, NeonSkill)

    def test_handle_data_erase(self):
        real_get_response = self.skill.get_response
        self.skill.get_response = Mock(return_value=False)

        selected_message = Message("test", {"dataset": "selected transcripts"})
        ignored_message = Message("test", {"dataset": "dislikes"})
        transcription_message = Message("test", {"dataset": "transcriptions"})
        brands_message = Message("test", {"dataset": "brands"})
        all_data_message = Message("test", {"dataset": "information"})
        media_message = Message("test", {"dataset": "pictures and videos"})
        units_message = Message("test", {"dataset": "format"})
        language_message = Message("test", {"dataset": "language settings"})
        cache_message = Message("test", {"dataset": "cached data"})
        profile_message = Message("test", {"dataset": "profile"})
        invalid_message = Message("test", {"dataset": "invalid setting"})

        self.skill.handle_data_erase(invalid_message)
        self.skill.speak_dialog.assert_not_called()

        def _check_get_response(opt, confirmed):
            call = self.skill.get_response.call_args[0]
            self.assertEqual(call[0], "ask_clear_data")
            self.assertEqual(set(call[1].keys()), {"option", "confirm"})
            self.assertEqual(call[1]["option"], self.skill.translate(opt))
            self.assertTrue(call[2](call[1]["confirm"]))
            if not confirmed:
                self.skill.speak_dialog.assert_called_with("confirm_no_action",
                                                           private=True)

        self.skill.handle_data_erase(selected_message)
        _check_get_response("word_liked_brands", False)

        self.skill.handle_data_erase(ignored_message)
        _check_get_response("word_disliked_brands", False)

        self.skill.handle_data_erase(transcription_message)
        _check_get_response("word_transcriptions", False)

        self.skill.handle_data_erase(brands_message)
        _check_get_response("word_all_brands", False)

        self.skill.handle_data_erase(all_data_message)
        _check_get_response("word_all_data", False)

        self.skill.handle_data_erase(media_message)
        _check_get_response("word_media", False)

        self.skill.handle_data_erase(units_message)
        _check_get_response("word_units", False)

        self.skill.handle_data_erase(language_message)
        _check_get_response("word_language", False)

        self.skill.handle_data_erase(cache_message)
        _check_get_response("word_caches", False)

        self.skill.handle_data_erase(profile_message)
        _check_get_response("word_profile_data", False)

        bus_event = Event()
        clear_data_message = None

        def _handle_data_clear(message):
            nonlocal clear_data_message
            clear_data_message = message
            bus_event.set()

        self.skill.bus.on("neon.clear_data", _handle_data_clear)
        self.skill.get_response = Mock(return_value=True)
        real_clear_user_data = self.skill._clear_user_data
        self.skill._clear_user_data = Mock()

        def _check_clear_user_data(dtype, message):
            self.skill._clear_user_data.assert_called_with(dtype, message)
            bus_event.wait(3)
            self.assertEqual(clear_data_message.context, message.context)
            self.assertEqual(clear_data_message.data["data_to_remove"],
                             [dtype.name])
            bus_event.clear()

        self.skill.handle_data_erase(invalid_message)
        self.skill._clear_user_data.assert_not_called()

        self.skill.handle_data_erase(selected_message)
        _check_get_response("word_liked_brands", True)
        _check_clear_user_data(
            self.skill.UserData.CONF_LIKES, selected_message)
        self.skill.handle_data_erase(ignored_message)
        _check_get_response("word_disliked_brands", True)
        _check_clear_user_data(
            self.skill.UserData.CONF_DISLIKES, ignored_message
        )
        self.skill.handle_data_erase(transcription_message)
        _check_get_response("word_transcriptions", True)
        _check_clear_user_data(
            self.skill.UserData.ALL_TR, transcription_message
        )
        self.skill.handle_data_erase(brands_message)
        _check_get_response("word_all_brands", True)
        self.skill._clear_user_data.assert_has_calls([
            call(self.skill.UserData.CONF_LIKES, brands_message),
            call(self.skill.UserData.CONF_DISLIKES, brands_message)
        ])
        bus_event.wait(5)
        self.assertEqual(clear_data_message.context, brands_message.context)
        self.assertEqual(clear_data_message.data["data_to_remove"],
                         ["CONF_LIKES", "CONF_DISLIKES"])
        bus_event.clear()
        self.skill.handle_data_erase(all_data_message)
        _check_get_response("word_all_data", True)
        _check_clear_user_data(
            self.skill.UserData.ALL_DATA, all_data_message
        )
        self.skill.handle_data_erase(media_message)
        _check_get_response("word_media", True)
        _check_clear_user_data(
            self.skill.UserData.ALL_MEDIA, media_message
        )
        self.skill.handle_data_erase(units_message)
        _check_get_response("word_units", True)
        _check_clear_user_data(
            self.skill.UserData.ALL_UNITS, units_message
        )
        self.skill.handle_data_erase(language_message)
        _check_get_response("word_language", True)
        _check_clear_user_data(
            self.skill.UserData.ALL_LANGUAGE, language_message
        )
        self.skill.handle_data_erase(cache_message)
        _check_get_response("word_caches", True)
        _check_clear_user_data(
            self.skill.UserData.CACHES, cache_message
        )
        self.skill.handle_data_erase(profile_message)
        _check_get_response("word_profile_data", True)
        _check_clear_user_data(
            self.skill.UserData.PROFILE, profile_message
        )

        self.skill.get_response = real_get_response
        self.skill._clear_user_data = real_clear_user_data

    def test_clear_user_data(self):
        test_config_path = join(dirname(__file__), "test_config",
                                "test_config.yml")
        shutil.copy2(test_config_path, join(dirname(test_config_path),
                                            "ngi_user_info.yml"))
        test_config = get_neon_user_config(join(dirname(__file__),
                                                "test_config"))
        username = test_config["user"]["username"]
        test_message = Message("test", {"key": "val"},
                               {"username": username,
                                "user_profiles": [test_config]})
        default_user_config = get_neon_user_config(self.skill.file_system.path)

        real_update_profile = self.skill.update_profile
        self.skill.update_profile = Mock()

        self.skill._clear_user_data(self.skill.UserData.ALL_DATA,
                                    test_message)
        self.skill.speak_dialog.assert_called_with("confirm_clear_all",
                                                   private=True)
        self.skill.update_profile.assert_called_with(
            default_user_config.content, test_message)

        self.skill._clear_user_data(self.skill.UserData.CONF_LIKES,
                                    test_message)
        self.skill.speak_dialog.assert_called_with(
            "confirm_clear_data",
            {"kind": self.skill.translate("word_liked_brands")},
            private=True
        )
        self.skill._clear_user_data(self.skill.UserData.CONF_DISLIKES,
                                    test_message)
        self.skill.speak_dialog.assert_called_with(
            "confirm_clear_data",
            {"kind": self.skill.translate("word_disliked_brands")},
            private=True
        )
        self.skill.update_profile.assert_called_with(
            {"brands": {"ignored_brands": {}}}, test_message
        )
        self.skill._clear_user_data(self.skill.UserData.ALL_TR,
                                    test_message)
        self.skill.speak_dialog.assert_called_with(
            "confirm_clear_data",
            {"kind": self.skill.translate("word_transcriptions")},
            private=True
        )
        self.skill._clear_user_data(self.skill.UserData.PROFILE,
                                    test_message)
        self.skill.speak_dialog.assert_called_with(
            "confirm_clear_data",
            {"kind": self.skill.translate("word_profile_data")},
            private=True
        )
        self.skill.update_profile.assert_called_with(
            {"user": default_user_config["user"]}, test_message
        )
        self.skill._clear_user_data(self.skill.UserData.CACHES,
                                    test_message)
        self.skill.speak_dialog.assert_called_with(
            "confirm_clear_data",
            {"kind": self.skill.translate("word_caches")},
            private=True
        )
        self.skill._clear_user_data(self.skill.UserData.ALL_UNITS,
                                    test_message)
        self.skill.speak_dialog.assert_called_with(
            "confirm_clear_data",
            {"kind": self.skill.translate("word_units")},
            private=True
        )
        self.skill.update_profile.assert_called_with(
            {"units": default_user_config["units"]}, test_message
        )
        self.skill._clear_user_data(self.skill.UserData.ALL_MEDIA,
                                    test_message)
        self.skill.speak_dialog.assert_called_with(
            "confirm_clear_data",
            {"kind": self.skill.translate("word_media")},
            private=True
        )
        self.skill._clear_user_data(self.skill.UserData.ALL_LANGUAGE,
                                    test_message)
        self.skill.speak_dialog.assert_called_with(
            "confirm_clear_data",
            {"kind": self.skill.translate("word_language")},
            private=True
        )
        self.skill.update_profile.assert_called_with(
            {"speech": default_user_config["speech"]}, test_message
        )

        self.skill.update_profile = real_update_profile
        os.remove(test_config.file_path)
        os.remove(join(test_config.path, ".ngi_user_info.tmp"))


if __name__ == '__main__':
    pytest.main()
