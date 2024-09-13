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
from ovos_bus_client.message import Message
from neon_utils.skills.neon_skill import NeonSkill
from neon_utils.validator_utils import numeric_confirmation_validator
from neon_utils.configuration_utils import get_user_config_from_mycroft_conf
from neon_utils.user_utils import get_message_user
from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements

from ovos_workshop.decorators import intent_handler


class DataControlsSkill(NeonSkill):
    # TODO: Refactor into separate module
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

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(network_before_load=False,
                                   internet_before_load=False,
                                   gui_before_load=False,
                                   requires_internet=False,
                                   requires_network=False,
                                   requires_gui=False,
                                   no_internet_fallback=True,
                                   no_network_fallback=True,
                                   no_gui_fallback=True)

    @intent_handler("clear_data.intent")
    def handle_data_erase(self, message: Message):
        """
        Handles a request to clear user data.
        This action will be confirmed numerically before executing
        :param message: Message associated with request
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
        elif self.voc_match(opt, "units"):
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
                user = get_message_user(message) or "local"
                for dtype in to_clear:
                    self._clear_user_data(dtype, message, user)

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
                         message: Message, username: str):
        """
        Speaks a confirmation and performs any necessary profile updates for the
        requested `data_type`.
        :param data_type: UserData to clear
        :param message: Message associated with request
        :param username: string username to update profile for
        """
        default_config = get_user_config_from_mycroft_conf()
        default_config["user"]["username"] = username
        LOG.info(f"Clearing profile for: {username}")
        if data_type == self.UserData.ALL_DATA:
            self.speak_dialog("confirm_clear_all", private=True)
            self.update_profile(default_config, message)
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
            updated_config = default_config["user"]
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
            updated_config = default_config["units"]
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
            updated_config = default_config["speech"]
            self.update_profile({"speech": updated_config}, message)
            return
