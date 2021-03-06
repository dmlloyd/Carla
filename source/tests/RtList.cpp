/*
 * Carla Tests
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

#include "RtList.hpp"

#include "CarlaString.hpp"
#include "CarlaMutex.hpp"

const unsigned short MIN_RT_EVENTS = 152;
const unsigned short MAX_RT_EVENTS = 512;

struct MyData {
    CarlaString str;
    int idStr;

    MyData()
        : idStr(-1) {}

    MyData(int id)
        : str(id),
          idStr(id) {}

#ifdef PROPER_CPP11_SUPPORT
    MyData(MyData&) = delete;
    MyData(const MyData&) = delete;
#endif
};

struct PostRtEvents {
    CarlaMutex mutex;
    RtList<MyData>::Pool dataPool;
    RtList<MyData> data;
    RtList<MyData> dataPendingRT;

    PostRtEvents()
        : dataPool(MIN_RT_EVENTS, MAX_RT_EVENTS),
          data(dataPool),
          dataPendingRT(dataPool) {}

    ~PostRtEvents()
    {
        clear();
    }

    void appendRT(const MyData& event)
    {
        dataPendingRT.append(event);
    }

    void clear()
    {
        mutex.lock();
        data.clear();
        dataPendingRT.clear();
        mutex.unlock();
    }

    void trySplice()
    {
        if (mutex.tryLock())
        {
            dataPendingRT.spliceAppend(data);
            mutex.unlock();
        }
    }

    //void appendNonRT(const PluginPostRtEvent& event)
    //{
    //    data.append_sleepy(event);
    //}

} postRtEvents;

void run5Tests()
{
    unsigned short k = 0;
    MyData allMyData[MAX_RT_EVENTS];

    // Make a safe copy of events while clearing them
    postRtEvents.mutex.lock();

    while (! postRtEvents.data.isEmpty())
    {
        MyData& my = postRtEvents.data.getFirst(true);
        allMyData[k++] = my;
        //std::memcpy(&allMyData[i++], &my, sizeof(MyData));
    }

    postRtEvents.mutex.unlock();

    printf("Post-Rt Event Count: %i\n", k);
    assert(k == 5);

    // data should be empty now
    assert(postRtEvents.data.count() == 0);
    assert(postRtEvents.data.isEmpty());
    assert(postRtEvents.dataPendingRT.count() == 0);
    assert(postRtEvents.dataPendingRT.isEmpty());

    // Handle events now
    for (unsigned short i=0; i < k; ++i)
    {
        const MyData& my = allMyData[i];

        printf("Got data: %i %s\n", my.idStr, (const char*)my.str);
    }
}

int main()
{
    MyData m1(1);
    MyData m2(2);
    MyData m3(3);
    MyData m4(4);
    MyData m5(5);

    // start
    assert(postRtEvents.data.count() == 0);
    assert(postRtEvents.data.isEmpty());
    assert(postRtEvents.dataPendingRT.count() == 0);
    assert(postRtEvents.dataPendingRT.isEmpty());

    // single append
    postRtEvents.appendRT(m1);
    postRtEvents.trySplice();
    assert(postRtEvents.data.count() == 1);
    assert(postRtEvents.dataPendingRT.count() == 0);

    // +3 appends
    postRtEvents.appendRT(m2);
    postRtEvents.appendRT(m4);
    postRtEvents.appendRT(m3);
    assert(postRtEvents.data.count() == 1);
    assert(postRtEvents.dataPendingRT.count() == 3);
    postRtEvents.trySplice();
    assert(postRtEvents.data.count() == 4);
    assert(postRtEvents.dataPendingRT.count() == 0);

    for (auto it = postRtEvents.data.begin(); it.valid(); it.next())
    {
        MyData& my(*it);

        printf("FOR DATA!!!: %i %s\n", my.idStr, (const char*)my.str);

        if (my.idStr == 1)
        {
            // +1 append at
            postRtEvents.dataPendingRT.insertAt(m5, it);
            assert(postRtEvents.data.count() == 4);
            assert(postRtEvents.dataPendingRT.count() == 1);
            postRtEvents.trySplice();
            assert(postRtEvents.data.count() == 5);
            assert(postRtEvents.dataPendingRT.count() == 0);
        }
    }

    run5Tests();

    // reset
    postRtEvents.clear();
    assert(postRtEvents.data.count() == 0);
    assert(postRtEvents.data.isEmpty());
    assert(postRtEvents.dataPendingRT.count() == 0);
    assert(postRtEvents.dataPendingRT.isEmpty());

    // test non-rt
    const unsigned int CARLA_EVENT_DATA_ATOM    = 0x01;
    const unsigned int CARLA_EVENT_DATA_MIDI_LL = 0x04;

    NonRtList<uint32_t> evIns, evOuts;
    evIns.append(CARLA_EVENT_DATA_ATOM);
    evOuts.append(CARLA_EVENT_DATA_ATOM);
    evOuts.append(CARLA_EVENT_DATA_MIDI_LL);

    if (evIns.count() > 0)
    {
        const size_t count(evIns.count());

        for (uint32_t j=0; j < count; ++j)
        {
            const uint32_t& type(evIns.getAt(j));

            if (type == CARLA_EVENT_DATA_ATOM)
                pass();
            else if (type == CARLA_EVENT_DATA_MIDI_LL)
                pass();
        }
    }

    evIns.clear();
    evOuts.clear();

    return 0;
}
