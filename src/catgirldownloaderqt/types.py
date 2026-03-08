# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Nyarch Linux

from enum import Enum


class NSFWOption(Enum):
    SHOW_EVERYTHING = "Show everything"
    ONLY_NSFW = "Only NSFW"
    BLOCK_NSFW = "Block NSFW"
