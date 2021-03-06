/*
 * DISTRHO Nekobi Plugin, based on Nekobee by Sean Bolton and others.
 * Copyright (C) 2013 Filipe Coelho <falktx@falktx.com>
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

#include "DistrhoUINekobi.hpp"

#include "dgl/ImageAboutWindow.hpp"

START_NAMESPACE_DISTRHO

// -------------------------------------------------

DistrhoUINekobi::DistrhoUINekobi()
    : OpenGLUI(),
      fAboutWindow(this)
{
    // FIXME
    fNeko.setTimerSpeed(4);

    // background
    fImgBackground = Image(DistrhoArtworkNekobi::backgroundData, DistrhoArtworkNekobi::backgroundWidth, DistrhoArtworkNekobi::backgroundHeight, GL_BGR);

    Image imageAbout(DistrhoArtworkNekobi::aboutData, DistrhoArtworkNekobi::aboutWidth, DistrhoArtworkNekobi::aboutHeight, GL_BGR);
    fAboutWindow.setImage(imageAbout);

    // slider
    Image sliderImage(DistrhoArtworkNekobi::sliderData, DistrhoArtworkNekobi::sliderWidth, DistrhoArtworkNekobi::sliderHeight);

    fSliderWaveform = new ImageSlider(this, sliderImage);
    fSliderWaveform->setStartPos(133, 40);
    fSliderWaveform->setEndPos(133, 60);
    fSliderWaveform->setRange(0.0f, 1.0f);
    fSliderWaveform->setValue(0.0f);
    fSliderWaveform->setIsSwitch(true);
    fSliderWaveform->setCallback(this);

    // knobs
    Image knobImage(DistrhoArtworkNekobi::knobData, DistrhoArtworkNekobi::knobWidth, DistrhoArtworkNekobi::knobHeight);

    // knob Tuning
    fKnobTuning = new ImageKnob(this, knobImage);
    fKnobTuning->setPos(41, 43);
    fKnobTuning->setRange(-12.0f, 12.0f);
    fKnobTuning->setValue(0.0f);
    fKnobTuning->setRotationAngle(305);
    fKnobTuning->setCallback(this);

    // knob Cutoff
    fKnobCutoff = new ImageKnob(this, knobImage);
    fKnobCutoff->setPos(185, 43);
    fKnobCutoff->setRange(0.0f, 100.0f);
    fKnobCutoff->setValue(25.0f);
    fKnobCutoff->setRotationAngle(305);
    fKnobCutoff->setCallback(this);

    // knob Resonance
    fKnobResonance = new ImageKnob(this, knobImage);
    fKnobResonance->setPos(257, 43);
    fKnobResonance->setRange(0.0f, 95.0f);
    fKnobResonance->setValue(25.0f);
    fKnobResonance->setRotationAngle(305);
    fKnobResonance->setCallback(this);

    // knob Env Mod
    fKnobEnvMod = new ImageKnob(this, knobImage);
    fKnobEnvMod->setPos(329, 43);
    fKnobEnvMod->setRange(0.0f, 100.0f);
    fKnobEnvMod->setValue(50.0f);
    fKnobEnvMod->setRotationAngle(305);
    fKnobEnvMod->setCallback(this);

    // knob Decay
    fKnobDecay = new ImageKnob(this, knobImage);
    fKnobDecay->setPos(400, 43);
    fKnobDecay->setRange(0.0f, 100.0f);
    fKnobDecay->setValue(75.0f);
    fKnobDecay->setRotationAngle(305);
    fKnobDecay->setCallback(this);

    // knob Accent
    fKnobAccent = new ImageKnob(this, knobImage);
    fKnobAccent->setPos(473, 43);
    fKnobAccent->setRange(0.0f, 100.0f);
    fKnobAccent->setValue(25.0f);
    fKnobAccent->setRotationAngle(305);
    fKnobAccent->setCallback(this);

    // knob Volume
    fKnobVolume = new ImageKnob(this, knobImage);
    fKnobVolume->setPos(545, 43);
    fKnobVolume->setRange(0.0f, 100.0f);
    fKnobVolume->setValue(75.0f);
    fKnobVolume->setRotationAngle(305);
    fKnobVolume->setCallback(this);

    // about button
    Image aboutImageNormal(DistrhoArtworkNekobi::aboutButtonNormalData, DistrhoArtworkNekobi::aboutButtonNormalWidth, DistrhoArtworkNekobi::aboutButtonNormalHeight);
    Image aboutImageHover(DistrhoArtworkNekobi::aboutButtonHoverData, DistrhoArtworkNekobi::aboutButtonHoverWidth, DistrhoArtworkNekobi::aboutButtonHoverHeight);
    fButtonAbout = new ImageButton(this, aboutImageNormal, aboutImageHover, aboutImageHover);
    fButtonAbout->setPos(505, 5);
    fButtonAbout->setCallback(this);
}

DistrhoUINekobi::~DistrhoUINekobi()
{
    delete fSliderWaveform;
    delete fKnobTuning;
    delete fKnobCutoff;
    delete fKnobResonance;
    delete fKnobEnvMod;
    delete fKnobDecay;
    delete fKnobAccent;
    delete fKnobVolume;
    delete fButtonAbout;
}

// -------------------------------------------------
// DSP Callbacks

void DistrhoUINekobi::d_parameterChanged(uint32_t index, float value)
{
    switch (index)
    {
    case DistrhoPluginNekobi::paramTuning:
        fKnobTuning->setValue(value);
        break;
    case DistrhoPluginNekobi::paramWaveform:
        fSliderWaveform->setValue(value);
        break;
    case DistrhoPluginNekobi::paramCutoff:
        fKnobCutoff->setValue(value);
        break;
    case DistrhoPluginNekobi::paramResonance:
        fKnobResonance->setValue(value);
        break;
    case DistrhoPluginNekobi::paramEnvMod:
        fKnobEnvMod->setValue(value);
        break;
    case DistrhoPluginNekobi::paramDecay:
        fKnobDecay->setValue(value);
        break;
    case DistrhoPluginNekobi::paramAccent:
        fKnobAccent->setValue(value);
        break;
    case DistrhoPluginNekobi::paramVolume:
        fKnobVolume->setValue(value);
        break;
    }
}

void DistrhoUINekobi::d_noteReceived(bool onOff, uint8_t, uint8_t note, uint8_t)
{
    return;

    (void)onOff;
    (void)note;
}

// ---------------------------------------------
// UI Callbacks

void DistrhoUINekobi::d_uiIdle()
{
    if (fNeko.idle())
        repaint();
}

// -------------------------------------------------
// Widget Callbacks

void DistrhoUINekobi::imageButtonClicked(ImageButton* button, int)
{
    if (button != fButtonAbout)
        return;

    fAboutWindow.exec();
}

void DistrhoUINekobi::imageKnobDragStarted(ImageKnob* knob)
{
    if (knob == fKnobTuning)
        d_editParameter(DistrhoPluginNekobi::paramTuning, true);
    else if (knob == fKnobCutoff)
        d_editParameter(DistrhoPluginNekobi::paramCutoff, true);
    else if (knob == fKnobResonance)
        d_editParameter(DistrhoPluginNekobi::paramResonance, true);
    else if (knob == fKnobEnvMod)
        d_editParameter(DistrhoPluginNekobi::paramEnvMod, true);
    else if (knob == fKnobDecay)
        d_editParameter(DistrhoPluginNekobi::paramDecay, true);
    else if (knob == fKnobAccent)
        d_editParameter(DistrhoPluginNekobi::paramAccent, true);
    else if (knob == fKnobVolume)
        d_editParameter(DistrhoPluginNekobi::paramVolume, true);
}

void DistrhoUINekobi::imageKnobDragFinished(ImageKnob* knob)
{
    if (knob == fKnobTuning)
        d_editParameter(DistrhoPluginNekobi::paramTuning, false);
    else if (knob == fKnobCutoff)
        d_editParameter(DistrhoPluginNekobi::paramCutoff, false);
    else if (knob == fKnobResonance)
        d_editParameter(DistrhoPluginNekobi::paramResonance, false);
    else if (knob == fKnobEnvMod)
        d_editParameter(DistrhoPluginNekobi::paramEnvMod, false);
    else if (knob == fKnobDecay)
        d_editParameter(DistrhoPluginNekobi::paramDecay, false);
    else if (knob == fKnobAccent)
        d_editParameter(DistrhoPluginNekobi::paramAccent, false);
    else if (knob == fKnobVolume)
        d_editParameter(DistrhoPluginNekobi::paramVolume, false);
}

void DistrhoUINekobi::imageKnobValueChanged(ImageKnob* knob, float value)
{
    if (knob == fKnobTuning)
        d_setParameterValue(DistrhoPluginNekobi::paramTuning, value);
    else if (knob == fKnobCutoff)
        d_setParameterValue(DistrhoPluginNekobi::paramCutoff, value);
    else if (knob == fKnobResonance)
        d_setParameterValue(DistrhoPluginNekobi::paramResonance, value);
    else if (knob == fKnobEnvMod)
        d_setParameterValue(DistrhoPluginNekobi::paramEnvMod, value);
    else if (knob == fKnobDecay)
        d_setParameterValue(DistrhoPluginNekobi::paramDecay, value);
    else if (knob == fKnobAccent)
        d_setParameterValue(DistrhoPluginNekobi::paramAccent, value);
    else if (knob == fKnobVolume)
        d_setParameterValue(DistrhoPluginNekobi::paramVolume, value);
}

void DistrhoUINekobi::imageSliderDragStarted(ImageSlider* slider)
{
    if (slider != fSliderWaveform)
        return;

    d_editParameter(DistrhoPluginNekobi::paramWaveform, true);
}

void DistrhoUINekobi::imageSliderDragFinished(ImageSlider* slider)
{
    if (slider != fSliderWaveform)
        return;

    d_editParameter(DistrhoPluginNekobi::paramWaveform, false);
}

void DistrhoUINekobi::imageSliderValueChanged(ImageSlider* slider, float value)
{
    if (slider != fSliderWaveform)
        return;

    d_setParameterValue(DistrhoPluginNekobi::paramWaveform, value);
}

void DistrhoUINekobi::onDisplay()
{
    fImgBackground.draw();
    fNeko.draw();
}

// -------------------------------------------------

UI* createUI()
{
    return new DistrhoUINekobi();
}

// -------------------------------------------------

END_NAMESPACE_DISTRHO
