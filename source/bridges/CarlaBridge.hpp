/*
 * Carla Bridge
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

#ifndef __CARLA_BRIDGE_HPP__
#define __CARLA_BRIDGE_HPP__

#include "CarlaDefines.hpp"

#define CARLA_BRIDGE_START_NAMESPACE namespace CarlaBridge {
#define CARLA_BRIDGE_END_NAMESPACE }
#define CARLA_BRIDGE_USE_NAMESPACE using namespace CarlaBridge;

CARLA_BRIDGE_START_NAMESPACE

// forward declarations of commonly used Carla-Bridge classes
class CarlaBridgeClient;
#ifdef BUILD_BRIDGE_UI
class CarlaBridgeToolkit;
#endif

CARLA_BRIDGE_END_NAMESPACE

#endif // __CARLA_BRIDGE_HPP__