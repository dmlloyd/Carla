/*
 * Carla Backend utils
 * Copyright (C) 2011-2013 Filipe Coelho <falktx@falktx.com>
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

#ifndef __CARLA_BACKEND_UTILS_HPP__
#define __CARLA_BACKEND_UTILS_HPP__

#include "CarlaBackend.hpp"
#include "CarlaString.hpp"

CARLA_BACKEND_START_NAMESPACE

// -------------------------------------------------

static inline
const char* BinaryType2Str(const BinaryType& type)
{
    switch (type)
    {
    case BINARY_NONE:
        return "BINARY_NONE";
    case BINARY_POSIX32:
        return "BINARY_POSIX32";
    case BINARY_POSIX64:
        return "BINARY_POSIX64";
    case BINARY_WIN32:
        return "BINARY_WIN32";
    case BINARY_WIN64:
        return "BINARY_WIN64";
    case BINARY_OTHER:
        return "BINARY_OTHER";
    }

    carla_stderr("CarlaBackend::BinaryType2Str(%i) - invalid type", type);
    return nullptr;
}

static inline
const char* PluginType2Str(const PluginType& type)
{
    switch (type)
    {
    case PLUGIN_NONE:
        return "PLUGIN_NONE";
    case PLUGIN_INTERNAL:
        return "PLUGIN_INTERNAL";
    case PLUGIN_LADSPA:
        return "PLUGIN_LADSPA";
    case PLUGIN_DSSI:
        return "PLUGIN_DSSI";
    case PLUGIN_LV2:
        return "PLUGIN_LV2";
    case PLUGIN_VST:
        return "PLUGIN_VST";
    case PLUGIN_GIG:
        return "PLUGIN_GIG";
    case PLUGIN_SF2:
        return "PLUGIN_SF2";
    case PLUGIN_SFZ:
        return "PLUGIN_SFZ";
    }

    carla_stderr("CarlaBackend::PluginType2Str(%i) - invalid type", type);
    return nullptr;
}

static inline
const char* PluginCategory2Str(const PluginCategory& category)
{
    switch (category)
    {
    case PLUGIN_CATEGORY_NONE:
        return "PLUGIN_CATEGORY_NONE";
    case PLUGIN_CATEGORY_SYNTH:
        return "PLUGIN_CATEGORY_SYNTH";
    case PLUGIN_CATEGORY_DELAY:
        return "PLUGIN_CATEGORY_DELAY";
    case PLUGIN_CATEGORY_EQ:
        return "PLUGIN_CATEGORY_EQ";
    case PLUGIN_CATEGORY_FILTER:
        return "PLUGIN_CATEGORY_FILTER";
    case PLUGIN_CATEGORY_DYNAMICS:
        return "PLUGIN_CATEGORY_DYNAMICS";
    case PLUGIN_CATEGORY_MODULATOR:
        return "PLUGIN_CATEGORY_MODULATOR";
    case PLUGIN_CATEGORY_UTILITY:
        return "PLUGIN_CATEGORY_UTILITY";
    case PLUGIN_CATEGORY_OTHER:
        return "PLUGIN_CATEGORY_OTHER";
    }

    carla_stderr("CarlaBackend::PluginCategory2Str(%i) - invalid category", category);
    return nullptr;
}

static inline
const char* ParameterType2Str(const ParameterType& type)
{
    switch (type)
    {
    case PARAMETER_UNKNOWN:
        return "PARAMETER_UNKNOWN";
    case PARAMETER_INPUT:
        return "PARAMETER_INPUT";
    case PARAMETER_OUTPUT:
        return "PARAMETER_OUTPUT";
    case PARAMETER_LATENCY:
        return "PARAMETER_LATENCY";
    case PARAMETER_SAMPLE_RATE:
        return "PARAMETER_SAMPLE_RATE";
#ifdef WANT_LV2
    case PARAMETER_LV2_FREEWHEEL:
        return "PARAMETER_LV2_FREEWHEEL";
    case PARAMETER_LV2_TIME:
        return "PARAMETER_LV2_TIME";
#endif
    }

    carla_stderr("CarlaBackend::ParameterType2Str(%i) - invalid type", type);
    return nullptr;
}

static inline
const char* InternalParametersIndex2Str(const InternalParametersIndex& index)
{
    switch (index)
    {
    case PARAMETER_NULL:
        return "PARAMETER_NULL";
    case PARAMETER_ACTIVE:
        return "PARAMETER_ACTIVE";
    case PARAMETER_DRYWET:
        return "PARAMETER_DRYWET";
    case PARAMETER_VOLUME:
        return "PARAMETER_VOLUME";
    case PARAMETER_BALANCE_LEFT:
        return "PARAMETER_BALANCE_LEFT";
    case PARAMETER_BALANCE_RIGHT:
        return "PARAMETER_BALANCE_RIGHT";
    case PARAMETER_PANNING:
        return "PARAMETER_PANNING";
    case PARAMETER_MAX:
        return "PARAMETER_MAX";
    }

    carla_stderr("CarlaBackend::InternalParametersIndex2Str(%i) - invalid index", index);
    return nullptr;
}

static inline
const char* OptionsType2Str(const OptionsType& type)
{
    switch (type)
    {
    case OPTION_PROCESS_NAME:
        return "OPTION_PROCESS_NAME";
    case OPTION_PROCESS_MODE:
        return "OPTION_PROCESS_MODE";
    case OPTION_FORCE_STEREO:
        return "OPTION_FORCE_STEREO";
    case OPTION_PREFER_PLUGIN_BRIDGES:
        return "OPTION_PREFER_PLUGIN_BRIDGES";
    case OPTION_PREFER_UI_BRIDGES:
        return "OPTION_PREFER_UI_BRIDGES";
#ifdef WANT_DSSI
    case OPTION_USE_DSSI_VST_CHUNKS:
        return "OPTION_USE_DSSI_VST_CHUNKS";
#endif
    case OPTION_MAX_PARAMETERS:
        return "OPTION_MAX_PARAMETERS";
    case OPTION_OSC_UI_TIMEOUT:
        return "OPTION_OSC_UI_TIMEOUT";
    case OPTION_PREFERRED_BUFFER_SIZE:
        return "OPTION_PREFERRED_BUFFER_SIZE";
    case OPTION_PREFERRED_SAMPLE_RATE:
        return "OPTION_PREFERRED_SAMPLE_RATE";
#ifndef BUILD_BRIDGE
    case OPTION_PATH_BRIDGE_NATIVE:
        return "OPTION_PATH_BRIDGE_NATIVE";
    case OPTION_PATH_BRIDGE_POSIX32:
        return "OPTION_PATH_BRIDGE_POSIX32";
    case OPTION_PATH_BRIDGE_POSIX64:
        return "OPTION_PATH_BRIDGE_POSIX64";
    case OPTION_PATH_BRIDGE_WIN32:
        return "OPTION_PATH_BRIDGE_WIN32";
    case OPTION_PATH_BRIDGE_WIN64:
        return "OPTION_PATH_BRIDGE_WIN64";
#endif
#ifdef WANT_LV2
    case OPTION_PATH_BRIDGE_LV2_GTK2:
        return "OPTION_PATH_BRIDGE_LV2_GTK2";
    case OPTION_PATH_BRIDGE_LV2_GTK3:
        return "OPTION_PATH_BRIDGE_LV2_GTK3";
    case OPTION_PATH_BRIDGE_LV2_QT4:
        return "OPTION_PATH_BRIDGE_LV2_QT4";
    case OPTION_PATH_BRIDGE_LV2_QT5:
        return "OPTION_PATH_BRIDGE_LV2_QT5";
    case OPTION_PATH_BRIDGE_LV2_COCOA:
        return "OPTION_PATH_BRIDGE_LV2_COCOA";
    case OPTION_PATH_BRIDGE_LV2_WINDOWS:
        return "OPTION_PATH_BRIDGE_LV2_WINDOWS";
    case OPTION_PATH_BRIDGE_LV2_X11:
        return "OPTION_PATH_BRIDGE_LV2_X11";
#endif
#ifdef WANT_VST
    case OPTION_PATH_BRIDGE_VST_COCOA:
        return "OPTION_PATH_BRIDGE_VST_COCOA";
    case OPTION_PATH_BRIDGE_VST_HWND:
        return "OPTION_PATH_BRIDGE_VST_HWND";
    case OPTION_PATH_BRIDGE_VST_X11:
        return "OPTION_PATH_BRIDGE_VST_X11";
#endif
    }

    carla_stderr("CarlaBackend::OptionsType2Str(%i) - invalid type", type);
    return nullptr;
}

static inline
const char* CallbackType2Str(const CallbackType& type)
{
    switch (type)
    {
    case CALLBACK_DEBUG:
        return "CALLBACK_DEBUG";
    case CALLBACK_PLUGIN_ADDED:
        return "CALLBACK_PLUGIN_ADDED";
    case CALLBACK_PLUGIN_REMOVED:
        return "CALLBACK_PLUGIN_REMOVED";
    case CALLBACK_PARAMETER_VALUE_CHANGED:
        return "CALLBACK_PARAMETER_VALUE_CHANGED";
    case CALLBACK_PARAMETER_DEFAULT_CHANGED:
        return "CALLBACK_PARAMETER_DEFAULT_CHANGED";
    case CALLBACK_PARAMETER_MIDI_CHANNEL_CHANGED:
        return "CALLBACK_PARAMETER_MIDI_CHANNEL_CHANGED";
    case CALLBACK_PARAMETER_MIDI_CC_CHANGED:
        return "CALLBACK_PARAMETER_MIDI_CC_CHANGED";
    case CALLBACK_PROGRAM_CHANGED:
        return "CALLBACK_PROGRAM_CHANGED";
    case CALLBACK_MIDI_PROGRAM_CHANGED:
        return "CALLBACK_MIDI_PROGRAM_CHANGED";
    case CALLBACK_NOTE_ON:
        return "CALLBACK_NOTE_ON";
    case CALLBACK_NOTE_OFF:
        return "CALLBACK_NOTE_OFF";
    case CALLBACK_SHOW_GUI:
        return "CALLBACK_SHOW_GUI";
    case CALLBACK_UPDATE:
        return "CALLBACK_UPDATE";
    case CALLBACK_RELOAD_INFO:
        return "CALLBACK_RELOAD_INFO";
    case CALLBACK_RELOAD_PARAMETERS:
        return "CALLBACK_RELOAD_PARAMETERS";
    case CALLBACK_RELOAD_PROGRAMS:
        return "CALLBACK_RELOAD_PROGRAMS";
    case CALLBACK_RELOAD_ALL:
        return "CALLBACK_RELOAD_ALL";
    case CALLBACK_NSM_ANNOUNCE:
        return "CALLBACK_NSM_ANNOUNCE";
    case CALLBACK_NSM_OPEN1:
        return "CALLBACK_NSM_OPEN1";
    case CALLBACK_NSM_OPEN2:
        return "CALLBACK_NSM_OPEN2";
    case CALLBACK_NSM_SAVE:
        return "CALLBACK_NSM_SAVE";
    case CALLBACK_ERROR:
        return "CALLBACK_ERROR";
    case CALLBACK_QUIT:
        return "CALLBACK_QUIT";
    }

    carla_stderr("CarlaBackend::CallbackType2Str(%i) - invalid type", type);
    return nullptr;
}

static inline
const char* ProcessMode2Str(const ProcessMode& mode)
{
    switch (mode)
    {
    case PROCESS_MODE_SINGLE_CLIENT:
        return "PROCESS_MODE_SINGLE_CLIENT";
    case PROCESS_MODE_MULTIPLE_CLIENTS:
        return "PROCESS_MODE_MULTIPLE_CLIENTS";
    case PROCESS_MODE_CONTINUOUS_RACK:
        return "PROCESS_MODE_CONTINUOUS_RACK";
    case PROCESS_MODE_PATCHBAY:
        return "PROCESS_MODE_PATCHBAY";
    case PROCESS_MODE_BRIDGE:
        return "PROCESS_MODE_BRIDGE";
    }

    carla_stderr("CarlaBackend::ProcessModeType2Str(%i) - invalid type", mode);
    return nullptr;
}

// -------------------------------------------------

static inline
uintptr_t getAddressFromPointer(void* ptr)
{
    carla_debug("CarlaBackend::getAddressFromPointer(%p)", ptr);
    CARLA_ASSERT(ptr != nullptr);

    uintptr_t* addr = (uintptr_t*)&ptr;
    return *addr;
}

static inline
void* getPointerFromAddress(uintptr_t& addr)
{
    CARLA_ASSERT(addr != 0);

    uintptr_t** const ptr = (uintptr_t**)&addr;
    return *ptr;
}

// -------------------------------------------------

static inline
const char* getPluginTypeString(const PluginType& type)
{
    carla_debug("CarlaBackend::getPluginTypeString(%s)", PluginType2Str(type));

    switch (type)
    {
    case PLUGIN_NONE:
        return "NONE";
    case PLUGIN_INTERNAL:
        return "INTERNAL";
    case PLUGIN_LADSPA:
        return "LADSPA";
    case PLUGIN_DSSI:
        return "DSSI";
    case PLUGIN_LV2:
        return "LV2";
    case PLUGIN_VST:
        return "VST";
    case PLUGIN_GIG:
        return "GIG";
    case PLUGIN_SF2:
        return "SF2";
    case PLUGIN_SFZ:
        return "SFZ";
    }

    carla_stderr("CarlaBackend::getPluginTypeString(%i) - invalid type", type);
    return "NONE";
}

// -------------------------------------------------

static inline
PluginCategory getPluginCategoryFromName(const char* const name)
{
    carla_debug("CarlaBackend::getPluginCategoryFromName(\"%s\")", name);
    CARLA_ASSERT(name);

    if (! name)
        return PLUGIN_CATEGORY_NONE;

    CarlaString sname(name);

    if (sname.isEmpty())
        return PLUGIN_CATEGORY_NONE;

    sname.toLower();

    // generic tags first
    if (sname.contains("delay"))
        return PLUGIN_CATEGORY_DELAY;
    if (sname.contains("reverb"))
        return PLUGIN_CATEGORY_DELAY;

    // filter
    if (sname.contains("filter"))
        return PLUGIN_CATEGORY_FILTER;

    // dynamics
    if (sname.contains("dynamics"))
        return PLUGIN_CATEGORY_DYNAMICS;
    if (sname.contains("amplifier"))
        return PLUGIN_CATEGORY_DYNAMICS;
    if (sname.contains("compressor"))
        return PLUGIN_CATEGORY_DYNAMICS;
    if (sname.contains("enhancer"))
        return PLUGIN_CATEGORY_DYNAMICS;
    if (sname.contains("exciter"))
        return PLUGIN_CATEGORY_DYNAMICS;
    if (sname.contains("gate"))
        return PLUGIN_CATEGORY_DYNAMICS;
    if (sname.contains("limiter"))
        return PLUGIN_CATEGORY_DYNAMICS;

    // modulator
    if (sname.contains("modulator"))
        return PLUGIN_CATEGORY_MODULATOR;
    if (sname.contains("chorus"))
        return PLUGIN_CATEGORY_MODULATOR;
    if (sname.contains("flanger"))
        return PLUGIN_CATEGORY_MODULATOR;
    if (sname.contains("phaser"))
        return PLUGIN_CATEGORY_MODULATOR;
    if (sname.contains("saturator"))
        return PLUGIN_CATEGORY_MODULATOR;

    // utility
    if (sname.contains("utility"))
        return PLUGIN_CATEGORY_UTILITY;
    if (sname.contains("analyzer"))
        return PLUGIN_CATEGORY_UTILITY;
    if (sname.contains("converter"))
        return PLUGIN_CATEGORY_UTILITY;
    if (sname.contains("deesser"))
        return PLUGIN_CATEGORY_UTILITY;
    if (sname.contains("mixer"))
        return PLUGIN_CATEGORY_UTILITY;

    // common tags
    if (sname.contains("verb"))
        return PLUGIN_CATEGORY_DELAY;

    if (sname.contains("eq"))
        return PLUGIN_CATEGORY_EQ;

    if (sname.contains("tool"))
        return PLUGIN_CATEGORY_UTILITY;

    return PLUGIN_CATEGORY_NONE;
}

CARLA_BACKEND_END_NAMESPACE

#endif // __CARLA_BACKEND_UTILS_HPP__