import pyNN.spiNNaker as sim
import pyNN.utility.plotting as plot
import matplotlib.pyplot as plt
import threading
from time import sleep
from pykeyboard import PyKeyboard
import cv2
import numpy as np
import pyautogui
from datetime import datetime


sim.setup(timestep=1.0)
sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 100)

input1 = sim.Population(3, sim.external_devices.SpikeInjector(), label="stateSpikeInjector")

pre_pop = sim.Population(3, sim.IF_curr_exp(tau_syn_E=100, tau_refrac=50), label="statePopulation")
post_pop = sim.Population(3, sim.IF_curr_exp(tau_syn_E=25, tau_refrac=100), label="actorPopulation")

sim.external_devices.activate_live_output_for(pre_pop, database_notify_host="localhost", database_notify_port_num=19996)
sim.external_devices.activate_live_output_for(input1, database_notify_host="localhost", database_notify_port_num=19998)
sim.external_devices.activate_live_output_for(post_pop, database_notify_host="localhost", database_notify_port_num=20000)

timing_rule = sim.SpikePairRule(tau_plus=50.0, tau_minus=50.0,
                                A_plus=0.001, A_minus=0.001)
weight_rule = sim.AdditiveWeightDependence(w_max=5.0, w_min=-5.0)
stdp_model = sim.STDPMechanism(timing_dependence=timing_rule,
                               weight_dependence=weight_rule,
                               weight=2, delay=1)
stdp_projection = sim.Projection(pre_pop, post_pop, sim.OneToOneConnector(),
                                 synapse_type=stdp_model)
input_projection1 = sim.Projection(input1, pre_pop, sim.OneToOneConnector(),
                            synapse_type=sim.StaticSynapse(weight=5, delay=1))

pre_pop.record(["spikes", "v"])
post_pop.record(["spikes", "v"])

k = PyKeyboard()


def receive_spikes(label, time, neuron_ids):
    try:
        time = datetime.time(datetime.now())
        for neuron_id in neuron_ids:
            if str(neuron_id) is '0':
                print str(time) + ' press right'
                k.press_key(k.right_key)
                sleep(1)
                print str(time) + ' release right'
                k.release_key(k.right_key)
            if str(neuron_id) is '1':
                print str(time) + ' press left'
                k.press_key(k.left_key)
                sleep(1)
                print str(time) + ' release left'
                k.release_key(k.left_key)
            if str(neuron_id) is '2':
                print str(time) + ' press space'
                k.press_key(k.space)
                sleep(1)
                print str(time) + ' release space'
                k.release_key(k.space)
    except RuntimeError:
        pass


numberOfSpikes = 1


live_spikes_connection = sim.external_devices.SpynnakerLiveSpikesConnection(
    receive_labels=["actorPopulation"], local_port=20000, send_labels=None)

live_spikes_connection2 = sim.external_devices.SpynnakerLiveSpikesConnection(
    receive_labels=None, local_port=19998, send_labels=['stateSpikeInjector'])

live_spikes_connection.add_receive_callback("actorPopulation", receive_spikes)


def send_spikes(id):
    live_spikes_connection2.send_spike('stateSpikeInjector', id,
                                       send_full_keys=True)


def send_right_press_spikes_thread():
    sleep(12)
    while True:
        try:
            time = datetime.time(datetime.now())
            print time
            image = pyautogui.screenshot(region=(0, 200, 1250, 700))
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            cv2.imwrite("screenCapture.png", image)
            meatboy_image = cv2.imread('meatboy.png')
            meatgirl_image = cv2.imread('meatgirl.png')
            large_image = cv2.imread("screenCapture.png")
            method = cv2.TM_SQDIFF_NORMED
            result = cv2.matchTemplate(meatboy_image.astype(np.float32), large_image.astype(np.float32), method)
            result2 = cv2.matchTemplate(meatgirl_image.astype(np.float32), large_image.astype(np.float32), method)
            mn, _, mnLoc, _ = cv2.minMaxLoc(result)
            mn2, _, mnLoc2, _ = cv2.minMaxLoc(result2)
            MPx, MPy = mnLoc
            MPx2, MPy2 = mnLoc2

            xOffset = MPx2 - MPx
            yOffset = MPy2 - MPy
            # print str(time) + ' X offset:' + str(xOffset)
            # print str(time) + ' Y offset:' + str(yOffset)
            # too much to the left
            if xOffset > 0:
                # press right
                send_spikes(0)
                # print str(time) + ' command press right'
            # too much to the right
            else:
                # press left
                send_spikes(1)
                # print str(time) + ' command press left'
            sleep(1)
        except AttributeError:
            pass


def send_left_press_spikes_thread():
    sleep(12)
    while True:
        try:
            time = datetime.time(datetime.now())
            print time
            image = pyautogui.screenshot(region=(0, 200, 1250, 700))
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            cv2.imwrite("screenCapture.png", image)
            meatboy_image = cv2.imread('meatboy.png')
            meatgirl_image = cv2.imread('meatgirl.png')
            large_image = cv2.imread("screenCapture.png")
            method = cv2.TM_SQDIFF_NORMED
            result = cv2.matchTemplate(meatboy_image.astype(np.float32), large_image.astype(np.float32), method)
            result2 = cv2.matchTemplate(meatgirl_image.astype(np.float32), large_image.astype(np.float32), method)
            mn, _, mnLoc, _ = cv2.minMaxLoc(result)
            mn2, _, mnLoc2, _ = cv2.minMaxLoc(result2)
            MPx, MPy = mnLoc
            MPx2, MPy2 = mnLoc2

            xOffset = MPx2 - MPx
            yOffset = MPy2 - MPy
            # print str(time) + ' X offset:' + str(xOffset)
            # print str(time) + ' Y offset:' + str(yOffset)
            # too much to the left
            if xOffset > 0:
                # press right
                send_spikes(0)
                # print str(time) + ' command press right'
            # too much to the right
            else:
                # press left
                send_spikes(1)
                # print str(time) + ' command press left'
            sleep(1)
        except AttributeError:
            pass


def send_jump_press_spikes_thread():
    sleep(12)
    while True:
        try:
            time = datetime.time(datetime.now())
            print time
            image = pyautogui.screenshot(region=(0, 200, 1250, 700))
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            cv2.imwrite("screenCapture.png", image)
            meatboy_image = cv2.imread('meatboy.png')
            meatgirl_image = cv2.imread('meatgirl.png')
            large_image = cv2.imread("screenCapture.png")
            method = cv2.TM_SQDIFF_NORMED
            result = cv2.matchTemplate(meatboy_image.astype(np.float32), large_image.astype(np.float32), method)
            result2 = cv2.matchTemplate(meatgirl_image.astype(np.float32), large_image.astype(np.float32), method)
            mn, _, mnLoc, _ = cv2.minMaxLoc(result)
            mn2, _, mnLoc2, _ = cv2.minMaxLoc(result2)
            MPx, MPy = mnLoc
            MPx2, MPy2 = mnLoc2

            xOffset = MPx2 - MPx
            yOffset = MPy2 - MPy
            # print str(time) + ' X offset:' + str(xOffset)
            # print str(time) + ' Y offset:' + str(yOffset)
            # too much to the left
            if yOffset < 0:
                # too much to the left
                if xOffset > 0:
                    # press right
                    send_spikes(0)
                    # print str(time) + ' command press right'
                # too much to the right
                else:
                    # press left
                    send_spikes(1)
                    # print str(time) + ' command press left'
                # press space
                send_spikes(2)
                # print str(time) + ' command press space'
            sleep(2)
        except AttributeError:
            pass


thread0 = threading.Thread(target=send_right_press_spikes_thread)
thread2 = threading.Thread(target=send_left_press_spikes_thread)
thread4 = threading.Thread(target=send_jump_press_spikes_thread)

thread0.start()
thread2.start()
thread4.start()

initialWeights = stdp_projection.getWeights()

weightRight = []
weightLeft = []
weightJump = []

for i in range(5):
    sim.run(3000)
    sleep(1.5)
    time = datetime.time(datetime.now())
    print time
    weights = stdp_projection.getWeights()
    weightRight.append(weights[0])
    weightLeft.append(weights[1])
    weightJump.append(weights[2])

# neo = actorPopulation.get_data(variables=["spikes", "v"])
# spikes = neo.segments[0].spiketrains
# v = neo.segments[0].filter(name='v')[0]
neo = post_pop.get_data(variables=["spikes", "v"])
spikes2 = neo.segments[0].spiketrains
v2 = neo.segments[0].filter(name='v')[0]

sim.end()

plt.plot(weightRight, label='right weights')
plt.plot(weightLeft, label='left weights')
plt.plot(weightJump, label='jump weights')
plt.legend()
plt.show()

plot.Figure(
    plot.Panel(v2, ylabel="Membrane potential (mV)",
               data_labels=['controls'], yticks=True),
    plot.Panel(spikes2, yticks=True, markersize=5),
    title="Simple Example",
    annotations="Simulated with {}".format(sim.name())
)
plt.show()