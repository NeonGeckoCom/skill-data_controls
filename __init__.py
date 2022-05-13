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

from random import randint
from adapt.intent import IntentBuilder
from mycroft_bus_client import Message
from neon_utils.logger import LOG
from neon_utils.skills.neon_skill import NeonSkill
from neon_utils.message_utils import request_from_mobile
from neon_utils.validator_utils import numeric_confirmation_validator
from neon_utils.configuration_utils import get_neon_user_config
from mycroft.skills import intent_handler

from .data_utils import refresh_neon, UserData


class DataControlsSkill(NeonSkill):
    def __init__(self):
        super(DataControlsSkill, self).__init__(name="DataControlsSkill")

    @intent_handler(IntentBuilder("clear_data_intent")
                    .require("ClearKeyword").require("dataset"))
    def handle_data_erase(self, message):
        """
        Handles a request to clear user data.
        This action will be confirmed numerically before executing
        :param message: message object associated with request
        """
        opt = str(message.data.get('dataset')).replace("user ", "")
        confirm_number = randint(100, 999)
        # LOG.info(self.confirm_number)
        LOG.info(opt)
        if opt in ['of']:  # Catch bad regex parsing
            utt = message.data['utterance']
            LOG.warning(utt)
            if " my " in utt:
                opt = utt.split("my ")[1]
            else:
                opt = utt
            LOG.info(opt)
        user = self.get_utterance_user(message)

        # Note that the below checks are ordered by request specificity
        if self.voc_match(opt, "Selected"):
            dialog_opt = "clear your transcribed likes"
            to_clear = (UserData.CONF_LIKES,)
        elif self.voc_match(opt, "Ignored"):
            dialog_opt = "clear your transcribed dislikes"
            to_clear = (UserData.CONF_DISLIKES,)
        elif self.voc_match(opt, "Transcription"):
            dialog_opt = "clear all of your transcriptions"
            to_clear = (UserData.ALL_TR,)
        elif self.voc_match(opt, "Brands"):
            dialog_opt = "clear all of your brands"
            to_clear = (UserData.CONF_LIKES, UserData.CONF_DISLIKES)
        elif self.voc_match(opt, "Media"):
            dialog_opt = "clear your user photos, videos, " \
                         "and audio recordings on this device"
            to_clear = (UserData.ALL_MEDIA,)
        elif self.voc_match(opt, "Language"):
            dialog_opt = "reset your language settings"
            to_clear = (UserData.ALL_LANGUAGE,)
        elif self.voc_match(opt, "Cache"):
            dialog_opt = "clear all of your cached responses"
            to_clear = (UserData.CACHES,)
        elif self.voc_match(opt, "Profile"):
            dialog_opt = "reset your user profile"
            to_clear = (UserData.PROFILE,)
        elif self.voc_match(opt, "Preferences"):
            dialog_opt = "reset your unit and interface preferences"
            to_clear = (UserData.ALL_PREFS,)
        elif self.voc_match(opt, "Data"):
            dialog_opt = "clear all of your data"
            to_clear = (UserData.ALL_DATA,)
        else:
            dialog_opt = None
            to_clear = None

        if dialog_opt:
            validator = numeric_confirmation_validator(str(confirm_number))
            if self.get_response('ClearData', {'option': dialog_opt,
                                               'confirm': str(confirm_number)},
                                 validator):
                for dtype in to_clear:
                    self._clear_user_data(user, dtype, message)
            else:
                self.speak_dialog("NotDoingAnything", private=True)
        else:
            LOG.warning(f"Invalid data type requested: {opt}")

    def _clear_user_data(self, user: str, data_type: UserData,
                         message: Message):
        """
        Clears the requested data_type for the specified user and speaks some
        confirmation.
        """
        refresh_neon(data_type, user)
        default_config = get_neon_user_config(self.file_system.path)
        if data_type == UserData.ALL_DATA:
            self.speak_dialog("ConfirmClearAll", private=True)
            self.update_profile(default_config.content, message)

            if request_from_mobile(message):
                self.mobile_skill_intent("clear_data",
                                         {"kind": "all"}, message)
            else:
                self.socket_emit_to_server("clear cookies intent",
                                           [message.context["klat_data"]
                                            ["request_id"]])
            return
        if data_type == UserData.CONF_LIKES:
            self.speak_dialog("ConfirmClearData", {"kind": "liked brands"},
                              private=True)
            return
        if data_type == UserData.CONF_DISLIKES:
            self.speak_dialog("ConfirmClearData", {"kind": "ignored brands"},
                              private=True)
            updated_config = {"brands": {"ignored_brands": {}}}
            self.update_profile(updated_config, message)
            return
        if data_type == UserData.ALL_TR:
            self.speak_dialog("ConfirmClearData",
                              {"kind": "audio recordings and transcriptions"},
                              private=True)
            return
        if data_type == UserData.PROFILE:
            self.speak_dialog("ConfirmClearData",
                              {"kind": "personal profile data"}, private=True)
            updated_config = default_config.content["user"]
            self.update_profile({"user": updated_config}, message)
            return
        if data_type == UserData.CACHES:
            self.speak_dialog("ConfirmClearData", {"kind": "cached responses"},
                              private=True)
            if request_from_mobile(message):
                self.mobile_skill_intent("clear_data", {"kind": "cache"},
                                         message)
            elif self.server:
                self.socket_emit_to_server("clear cookies intent",
                                           [message.context["klat_data"]
                                            ["request_id"]])
            return
        if data_type == UserData.ALL_PREFS:
            self.speak_dialog("ConfirmClearData", {"kind": "unit preferences"},
                              private=True)
            updated_config = default_config.content["units"]
            self.update_profile({"units": updated_config}, message)
            return
        if data_type == UserData.ALL_MEDIA:
            self.speak_dialog("ConfirmClearData",
                              {"kind": "pictures, videos, and "
                                       "audio recordings I have taken."},
                              private=True)
            if request_from_mobile(message):
                self.mobile_skill_intent("clear_data", {"kind": "media"},
                                         message)
            return
        if data_type == UserData.ALL_LANGUAGE:
            self.speak_dialog("ConfirmClearData",
                              {"kind": "language preferences"}, private=True)
            updated_config = default_config.content["language"]
            self.update_profile({"language": updated_config}, message)
            return


def create_skill():
    return DataControlsSkill()
