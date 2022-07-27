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

from glob import glob
from shutil import rmtree
from neon_utils.configuration_utils import get_neon_local_config, get_neon_device_type
from neon_utils.logger import LOG

LOCAL_CONF = get_neon_local_config()
ALL_TRANSCRIPTS = ("ts_transcripts", "ts_selected_transcripts", "ts_ignored_transcripts",
                   "ts_transcript_audio_segments")
ALL_MEDIA = ("music", "video", "pictures")


# TODO: Add unit tests for these! DM
def refresh_neon(data_to_remove: str, user: str):
    if data_to_remove == "all":
        remove_transcripts(ALL_TRANSCRIPTS, user)
        remove_media(ALL_MEDIA, user)
    elif data_to_remove == "ignored":
        remove_transcripts(tuple("ts_ignored_transcripts"), user)
    elif data_to_remove == "selected":
        remove_transcripts(tuple("ts_selected_transcripts"), user)
    elif data_to_remove == "brands":
        remove_transcripts(("ts_selected_transcripts", "ts_ignored_transcripts"), user)
    elif data_to_remove == "transcripts":
        remove_transcripts(ALL_TRANSCRIPTS, user)
    elif data_to_remove == "media":
        remove_media(ALL_MEDIA, user)
    elif data_to_remove == "caches":
        remove_cache(user)
    else:
        LOG.warning(f"Unknown data type: {data_to_remove}")


def remove_transcripts(directories: tuple, user: str):
    docs_dir = os.path.expanduser(LOCAL_CONF["dirVars"].get("docsDir", "~/Documents/NeonGecko"))
    for directory in directories:
        transcript_path = os.path.join(docs_dir, directory)
        if get_neon_device_type() == "server":
            user_transcripts = glob(os.path.join(transcript_path, f"{user}-*"))
            for transcript in user_transcripts:
                rmtree(transcript)
        else:
            rmtree(transcript_path)


def remove_media(media: tuple, user: str):
    media_locations = {"music": LOCAL_CONF["dirVars"]["musicDir"],
                       "pictures": LOCAL_CONF["dirVars"]["picsDir"],
                       "video": LOCAL_CONF["dirVars"]["videoDir"]}
    for kind in media:
        dir_to_clean = media_locations.get(kind)
        if dir_to_clean:
            if get_neon_device_type() == "server":
                # TODO: Remove media indexed by username
                pass
            else:
                rmtree(dir_to_clean)


def remove_cache(user):
    if get_neon_device_type() == "server" and user != "admin":
        LOG.warning(f"{user} not allowed to clear cache!")
        return
    if LOCAL_CONF["dirVars"].get("cacheDir"):
        rmtree(LOCAL_CONF["dirVars"]["cacheDir"])
