/*
 * Carla Bridge Toolkit, Gtk version
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

#include "CarlaBridgeClient.hpp"
#include "CarlaBridgeToolkit.hpp"

#if defined(BRIDGE_COCOA) || defined(BRIDGE_HWND) || defined(BRIDGE_X11)
# error Embed UI uses Qt
#endif

#include <gtk/gtk.h>
#include <QtCore/QSettings>

CARLA_BRIDGE_START_NAMESPACE

// -------------------------------------------------------------------------

#if defined(BRIDGE_GTK2)
static const char* const appName = "Carla-Gtk2UIs";
#elif defined(BRIDGE_GTK3)
static const char* const appName = "Carla-Gtk3UIs";
#else
static const char* const appName = "Carla-UIs";
#endif

static int    gargc = 0;
static char** gargv = nullptr;

// -------------------------------------------------------------------------

class CarlaToolkitGtk : public CarlaBridgeToolkit
{
public:
    CarlaToolkitGtk(CarlaBridgeClient* const client, const char* const uiTitle)
        : CarlaBridgeToolkit(client, uiTitle),
          fWindow(nullptr),
          fLastX(0),
          fLastY(0),
          fLastWidth(0),
          fLastHeight(0)
    {
        carla_debug("CarlaToolkitGtk::CarlaToolkitGtk(%p, \"%s\")", client, uiTitle);
    }

    ~CarlaToolkitGtk() override
    {
        CARLA_ASSERT(fWindow == nullptr);
        carla_debug("CarlaToolkitGtk::~CarlaToolkitGtk()");
    }

    void init() override
    {
        CARLA_ASSERT(fWindow == nullptr);
        carla_debug("CarlaToolkitGtk::init()");

        gtk_init(&gargc, &gargv);

        fWindow = gtk_window_new(GTK_WINDOW_TOPLEVEL);
        gtk_window_resize(GTK_WINDOW(fWindow), 30, 30);
        gtk_widget_hide(fWindow);
    }

    void exec(const bool showGui) override
    {
        CARLA_ASSERT(kClient != nullptr);
        CARLA_ASSERT(fWindow != nullptr);
        carla_debug("CarlaToolkitGtk::exec(%s)", bool2str(showGui));

        GtkWidget* const widget((GtkWidget*)kClient->getWidget());

        gtk_container_add(GTK_CONTAINER(fWindow), widget);

        gtk_window_set_resizable(GTK_WINDOW(fWindow), kClient->isResizable());
        gtk_window_set_title(GTK_WINDOW(fWindow), kUiTitle);

        {
            QSettings settings("falkTX", appName);

            if (settings.contains(QString("%1/pos_x").arg(kUiTitle)))
            {
                gtk_window_get_position(GTK_WINDOW(fWindow), &fLastX, &fLastY);

                bool hasX, hasY;
                fLastX = settings.value(QString("%1/pos_x").arg(kUiTitle), fLastX).toInt(&hasX);
                fLastY = settings.value(QString("%1/pos_y").arg(kUiTitle), fLastY).toInt(&hasY);

                if (hasX && hasY)
                    gtk_window_move(GTK_WINDOW(fWindow), fLastX, fLastY);

                if (kClient->isResizable())
                {
                    gtk_window_get_size(GTK_WINDOW(fWindow), &fLastWidth, &fLastHeight);

                    bool hasWidth, hasHeight;
                    fLastWidth  = settings.value(QString("%1/width").arg(kUiTitle), fLastWidth).toInt(&hasWidth);
                    fLastHeight = settings.value(QString("%1/height").arg(kUiTitle), fLastHeight).toInt(&hasHeight);

                    if (hasWidth && hasHeight)
                        gtk_window_resize(GTK_WINDOW(fWindow), fLastWidth, fLastHeight);
                }
            }

            if (settings.value("Engine/UIsAlwaysOnTop", true).toBool())
               gtk_window_set_keep_above(GTK_WINDOW(fWindow), true);
        }

        if (showGui)
            show();
        else
            kClient->sendOscUpdate();

        g_timeout_add(50, gtk_ui_timeout, this);
        g_signal_connect(fWindow, "destroy", G_CALLBACK(gtk_ui_destroy), this);

        // First idle
        handleTimeout();

        // Main loop
        gtk_main();
    }

    void quit() override
    {
        carla_debug("CarlaToolkitGtk::quit()");

        if (fWindow != nullptr)
        {
            gtk_widget_destroy(fWindow);
            fWindow = nullptr;

            gtk_main_quit();
        }
    }

    void show() override
    {
        CARLA_ASSERT(fWindow != nullptr);
        carla_debug("CarlaToolkitGtk::show()");

        if (fWindow != nullptr)
            gtk_widget_show_all(fWindow);
    }

    void hide() override
    {
        CARLA_ASSERT(fWindow != nullptr);
        carla_debug("CarlaToolkitGtk::hide()");

        if (fWindow != nullptr)
            gtk_widget_hide(fWindow);
    }

    void resize(int width, int height) override
    {
        CARLA_ASSERT(fWindow != nullptr);
        carla_debug("CarlaToolkitGtk::resize(%i, %i)", width, height);

        if (fWindow != nullptr)
            gtk_window_resize(GTK_WINDOW(fWindow), width, height);
    }

    // ---------------------------------------------------------------------

protected:
    GtkWidget* fWindow;

    gint fLastX;
    gint fLastY;
    gint fLastWidth;
    gint fLastHeight;

    void handleDestroy()
    {
        carla_debug("CarlaToolkitGtk::handleDestroy()");

        fWindow = nullptr;

        QSettings settings("falkTX", appName);
        settings.setValue(QString("%1/pos_x").arg(kUiTitle), fLastX);
        settings.setValue(QString("%1/pos_y").arg(kUiTitle), fLastY);
        settings.setValue(QString("%1/width").arg(kUiTitle), fLastWidth);
        settings.setValue(QString("%1/height").arg(kUiTitle), fLastHeight);
    }

    gboolean handleTimeout()
    {
        if (fWindow != nullptr)
        {
            gtk_window_get_position(GTK_WINDOW(fWindow), &fLastX, &fLastY);
            gtk_window_get_size(GTK_WINDOW(fWindow), &fLastWidth, &fLastHeight);
        }

        kClient->uiIdle();
        return kClient->oscIdle();
    }

    // ---------------------------------------------------------------------

private:
    static void gtk_ui_destroy(GtkWidget*, gpointer data)
    {
        CARLA_ASSERT(data != nullptr);

        if (CarlaToolkitGtk* const _this_ = (CarlaToolkitGtk*)data)
            _this_->handleDestroy();

        gtk_main_quit();
    }

    static gboolean gtk_ui_timeout(gpointer data)
    {
        CARLA_ASSERT(data != nullptr);

        if (CarlaToolkitGtk* const _this_ = (CarlaToolkitGtk*)data)
            return _this_->handleTimeout();

        return false;
    }
};

// -------------------------------------------------------------------------

CarlaBridgeToolkit* CarlaBridgeToolkit::createNew(CarlaBridgeClient* const client, const char* const uiTitle)
{
    return new CarlaToolkitGtk(client, uiTitle);
}

CARLA_BRIDGE_END_NAMESPACE
