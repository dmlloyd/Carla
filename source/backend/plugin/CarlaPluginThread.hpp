/*
 * Carla Plugin Thread
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

#ifndef __CARLA_PLUGIN_THREAD_HPP__
#define __CARLA_PLUGIN_THREAD_HPP__

#include "CarlaBackend.hpp"
#include "CarlaString.hpp"

#include <QtCore/QThread>

class QProcess;

CARLA_BACKEND_START_NAMESPACE

class CarlaPluginThread : public QThread
{
public:
    enum Mode {
        PLUGIN_THREAD_NULL,
        PLUGIN_THREAD_DSSI_GUI,
        PLUGIN_THREAD_LV2_GUI,
        PLUGIN_THREAD_VST_GUI,
        PLUGIN_THREAD_BRIDGE
    };

    CarlaPluginThread(CarlaEngine* const engine, CarlaPlugin* const plugin, const Mode mode = PLUGIN_THREAD_NULL);
    ~CarlaPluginThread();

    void setMode(const CarlaPluginThread::Mode mode);
    void setOscData(const char* const binary, const char* const label, const char* const extra1="", const char* const extra2="");

protected:
    void run();

private:
    CarlaEngine* const kEngine;
    CarlaPlugin* const kPlugin;

    Mode        fMode;
    CarlaString fBinary;
    CarlaString fLabel;
    CarlaString fExtra1;
    CarlaString fExtra2;
    QProcess*   fProcess;

    CARLA_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CarlaPluginThread)
};

CARLA_BACKEND_END_NAMESPACE

#endif // __CARLA_PLUGIN_THREAD_HPP__
