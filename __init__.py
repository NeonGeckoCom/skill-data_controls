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

from enum import IntEnum
from random import randint
from adapt.intent import IntentBuilder
from mycroft_bus_client import Message
from neon_utils.logger import LOG
from neon_utils.skills.neon_skill import NeonSkill
from neon_utils.validator_utils import numeric_confirmation_validator
from neon_utils.configuration_utils import get_neon_user_config
from neon_utils.user_utils import get_message_user
from mycroft.skills import intent_handler


class DataControlsSkill(NeonSkill):
    class UserData(IntEnum):
        CACHES = 0
        PROFILE = 1
        ALL_TR = 2
        CONF_LIKES = 3
        CONF_DISLIKES = 4
        ALL_DATA = 5
        ALL_MEDIA = 6
        ALL_UNITS = 7
        ALL_LANGUAGE = 8

    def __init__(self):
        super(DataControlsSkill, self).__init__(name="DataControlsSkill")

    @intent_handler(IntentBuilder("clear_data_intent")
                    .require("clear").require("dataset"))
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

        # TODO: Below default is patching a bug in neon_utils
        user = get_message_user(message) or "local"

        # Note that the below checks are ordered by request specificity
        if self.voc_match(opt, "likes"):
            dialog_opt = "word_liked_brands"
            to_clear = (self.UserData.CONF_LIKES,)
        elif self.voc_match(opt, "dislikes"):
            dialog_opt = "word_disliked_brands"
            to_clear = (self.UserData.CONF_DISLIKES,)
        elif self.voc_match(opt, "transcription"):
            dialog_opt = "word_transcriptions"
            to_clear = (self.UserData.ALL_TR,)
        elif self.voc_match(opt, "brands"):
            dialog_opt = "word_all_brands"
            to_clear = (self.UserData.CONF_LIKES, self.UserData.CONF_DISLIKES)
        elif self.voc_match(opt, "media"):
            dialog_opt = "word_media"
            to_clear = (self.UserData.ALL_MEDIA,)
        elif self.voc_match(opt, "language"):
            dialog_opt = "word_language"
            to_clear = (self.UserData.ALL_LANGUAGE,)
        elif self.voc_match(opt, "cache"):
            dialog_opt = "word_caches"
            to_clear = (self.UserData.CACHES,)
        elif self.voc_match(opt, "profile"):
            dialog_opt = "word_profile_data"
            to_clear = (self.UserData.PROFILE,)
        elif self.voc_match(opt, "Units"):
            dialog_opt = "word_units"
            to_clear = (self.UserData.ALL_UNITS,)
        elif self.voc_match(opt, "data"):
            dialog_opt = "word_all_data"
            to_clear = (self.UserData.ALL_DATA,)
        else:
            dialog_opt = None
            to_clear = None

        if dialog_opt:
            validator = numeric_confirmation_validator(str(confirm_number))
            resp = self.get_response('ask_clear_data',
                                     {'option': self.translate(dialog_opt),
                                      'confirm': str(confirm_number)},
                                     validator)
            LOG.info(resp)
            if resp:
                for dtype in to_clear:
                    self._clear_user_data(dtype, message)
                self.bus.emit(message.forward("neon.clear_data",
                                              {"username": user,
                                               "data_to_remove": [dtype.name
                                                                  for dtype in
                                                                  to_clear]}))
            else:
                self.speak_dialog("confirm_no_action", private=True)
        else:
            LOG.warning(f"Invalid data type requested: {opt}")

    def _clear_user_data(self, data_type: UserData,
                         message: Message):
        """
        Clears the requested data_type for the specified user and speaks some
        confirmation.
        """
        default_config = get_neon_user_config(self.file_system.path)
        if data_type == self.UserData.ALL_DATA:
            self.speak_dialog("confirm_clear_all", private=True)
            self.update_profile(default_config.content, message)
            return
        if data_type == self.UserData.CONF_LIKES:
            self.speak_dialog("confirm_clear_data",
                              {"kind": self.translate("word_liked_brands")},
                              private=True)
            return
        if data_type == self.UserData.CONF_DISLIKES:
            self.speak_dialog("confirm_clear_data",
                              {"kind": self.translate("word_disliked_brands")},
                              private=True)
            updated_config = {"brands": {"ignored_brands": {}}}
            self.update_profile(updated_config, message)
            return
        if data_type == self.UserData.ALL_TR:
            self.speak_dialog("confirm_clear_data",
                              {"kind": self.translate("word_transcriptions")},
                              private=True)
            return
        if data_type == self.UserData.PROFILE:
            self.speak_dialog("confirm_clear_data",
                              {"kind": self.translate("word_profile_data")},
                              private=True)
            updated_config = default_config.content["user"]
            self.update_profile({"user": updated_config}, message)
            return
        if data_type == self.UserData.CACHES:
            self.speak_dialog("confirm_clear_data",
                              {"kind": self.translate("word_caches")},
                              private=True)
            return
        if data_type == self.UserData.ALL_UNITS:
            self.speak_dialog("confirm_clear_data",
                              {"kind": self.translate("word_units")},
                              private=True)
            updated_config = default_config.content["units"]
            self.update_profile({"units": updated_config}, message)
            return
        if data_type == self.UserData.ALL_MEDIA:
            self.speak_dialog("confirm_clear_data",
                              {"kind": self.translate("word_media")},
                              private=True)
            return
        if data_type == self.UserData.ALL_LANGUAGE:
            self.speak_dialog("confirm_clear_data",
                              {"kind": self.translate("word_language")},
                              private=True)
            updated_config = default_config.content["speech"]
            self.update_profile({"speech": updated_config}, message)
            return


def create_skill():
    return DataControlsSkill()
