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

import shutil
import unittest
import pytest

from os import mkdir
from os.path import dirname, join, exists
from mock import Mock
from mycroft_bus_client import Message
from ovos_utils.messagebus import FakeBus
from neon_utils.configuration_utils import get_neon_local_config, get_neon_user_config

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

        # Override the configuration and fs paths to use the test directory
        cls.skill.local_config = get_neon_local_config(cls.test_fs)
        cls.skill.user_config = get_neon_user_config(cls.test_fs)
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
        preferences_message = Message("test", {"dataset": "settings"})
        language_message = Message("test", {"dataset": "language settings"})
        cache_message = Message("test", {"dataset": "cached data"})
        profile_message = Message("test", {"dataset": "profile"})
        invalid_message = Message("test", {"dataset": "invalid setting"})

        self.skill.handle_data_erase(invalid_message)
        self.skill.speak_dialog.assert_not_called()

        def _check_get_response(opt):
            call = self.skill.get_response.call_args[0]
            self.assertEqual(call[0], "ClearData")
            self.assertEqual(set(call[1].keys()), {"option", "confirm"})
            self.assertEqual(call[1]["option"], opt)
            self.assertTrue(call[2](call[1]["confirm"]))
            self.skill.speak_dialog.assert_called_with("NotDoingAnything",
                                                       private=True)

        self.skill.handle_data_erase(selected_message)
        _check_get_response("clear your transcribed likes")

        self.skill.handle_data_erase(ignored_message)
        _check_get_response("clear your transcribed dislikes")

        self.skill.handle_data_erase(transcription_message)
        _check_get_response("clear all of your transcriptions")

        self.skill.handle_data_erase(brands_message)
        _check_get_response("clear all of your brands")

        self.skill.handle_data_erase(all_data_message)
        _check_get_response("clear all of your data")

        self.skill.handle_data_erase(media_message)
        _check_get_response("clear your user photos, videos, "
                            "and audio recordings on this device")

        self.skill.handle_data_erase(preferences_message)
        _check_get_response("reset your unit and interface preferences")

        self.skill.handle_data_erase(language_message)
        _check_get_response("reset your language settings")

        self.skill.handle_data_erase(cache_message)
        _check_get_response("clear all of your cached responses")

        self.skill.handle_data_erase(profile_message)
        _check_get_response("reset your user profile")

        self.skill.get_response = Mock(return_value=True)
        real_clear_user_data = self.skill._clear_user_data
        self.skill._clear_user_data = Mock()
        # TODO: Test all calls to clear_user_data

        self.skill.get_response = real_get_response

    def test_clear_user_data(self):
        pass

    # TODO: Test data_utils


if __name__ == '__main__':
    pytest.main()
