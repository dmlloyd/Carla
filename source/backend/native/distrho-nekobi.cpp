/*
 * Carla Native Plugins
 * Copyright (C) 2012-2013 Filipe Coelho <falktx@falktx.com>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License, or any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * For a full copy of the GNU General Public License see the GPL.txt file
 */

#include "CarlaNative.hpp"

// Plugin Code
#include "nekobi/DistrhoArtworkNekobi.cpp"
#include "nekobi/DistrhoPluginNekobi.cpp"
#include "nekobi/DistrhoUINekobi.cpp"

// Carla DISTRHO Plugin
#include "distrho/DistrhoPluginCarla.cpp"

START_NAMESPACE_DISTRHO

// -----------------------------------------------------------------------

static const PluginDescriptor nekobiDesc = {
    /* category  */ PLUGIN_CATEGORY_EQ,
    /* hints     */ static_cast<PluginHints>(PLUGIN_IS_RTSAFE|PLUGIN_IS_SYNTH|PLUGIN_HAS_GUI),
    /* supports  */ static_cast<PluginSupports>(PLUGIN_SUPPORTS_CONTROL_CHANGES|PLUGIN_SUPPORTS_ALL_SOUND_OFF),
    /* audioIns  */ DISTRHO_PLUGIN_NUM_INPUTS,
    /* audioOuts */ DISTRHO_PLUGIN_NUM_OUTPUTS,
    /* midiIns   */ 1,
    /* midiOuts  */ 0,
    /* paramIns  */ DistrhoPluginNekobi::paramCount,
    /* paramOuts */ 0,
    /* name      */ DISTRHO_PLUGIN_NAME,
    /* label     */ "Nekobi",
    /* maker     */ "falkTX",
    /* copyright */ "GPL v2+",
    PluginDescriptorFILL(PluginCarla)
};

END_NAMESPACE_DISTRHO

// -----------------------------------------------------------------------

void carla_register_native_plugin_Nekobi()
{
    USE_NAMESPACE_DISTRHO
    carla_register_native_plugin(&nekobiDesc);
}

// -----------------------------------------------------------------------
